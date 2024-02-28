import datetime
import json
import os

import jwt
from langchain.schema import HumanMessage, SystemMessage
from langchain.vectorstores.chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Guider, Match, Plan, Traject, User
from .serializer import GuideSerializer, MatchSerializer, UserSerializer

CHROMA_PATH = "./api/data/chroma"
CHROMA_PATH2 = "./api/data/chroma2"


os.environ["OPENAI_API_KEY"] = "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"


class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LoginView(APIView):
    def post(self, request):
        email = request.data["email"]
        password = request.data["password"]

        user = User.objects.filter(email=email).first()

        if user is None:
            raise AuthenticationFailed("User not found!")

        if not user.check_password(password):
            raise AuthenticationFailed("Incorrect password!")

        payload = {
            "id": user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            "iat": datetime.datetime.utcnow(),
        }

        token = jwt.encode(payload, "secret", algorithm="HS256")

        response = Response()

        response.set_cookie(key="jwt", value=token, httponly=True)
        response.data = {"jwt": token}
        return response


class LogoutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie("jwt")
        response.data = {"message": "success"}
        return response


class UserInfo(APIView):
    def get(self, request):
        token = request.COOKIES.get("jwt")
        if not token:
            raise AuthenticationFailed("Unauthenticated!")

        try:
            payload = jwt.decode(token, "secret", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Unauthenticated!")

        user = User.objects.filter(id=payload["id"]).first()
        serializer = UserSerializer(user)
        return Response(serializer.data)


class TrajectDetail(APIView):
    def post(self, request):

        # Prepare the DB.
        embedding_function = OpenAIEmbeddings()
        db = Chroma(
            persist_directory=CHROMA_PATH, embedding_function=embedding_function
        )
        db2 = Chroma(
            persist_directory=CHROMA_PATH2, embedding_function=embedding_function
        )

        token = request.COOKIES.get("jwt")
        if not token:
            raise AuthenticationFailed("Unauthenticated!")

        try:
            payload = jwt.decode(token, "secret", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Unauthenticated!")
        user_id = payload["id"]

        budget = request.data.get("budget")
        ville1 = request.data.get("city")
        time = request.data.get("time")
        nombre = request.data.get("number")
        objectif = request.data.get("objectif")

        # -------------helping the search models with those statistics-----------------------#
        hebergement = int(budget) * 0.5
        restaurant = int(budget) * 0.3
        if 30 < restaurant < 150:
            rest = "1 fourchette"
        elif 150 <= restaurant < 300:
            rest = "2 fourchette"

        else:
            rest = "3 fourchette"

        if 100 <= hebergement < 150:
            hotel = "1 étoile"
        elif 150 <= hebergement < 250:
            hotel = "2 étoiles"
        elif 250 <= hebergement < 700:
            hotel = "3 étoiles"
        elif 700 <= hebergement < 800:
            hotel = "4 étoiles"
        else:
            hotel = "5 étoiles"
        # ---------------------------------------------------------------#

        # -------------------------questions-----------------------------#

        question1 = (
            f"give me  hotels in {ville1} and those hotels should be with {hotel} "
        )
        question2 = f"trouver tout les  {ville1} "

        # -------------------------embedding Models-----------------------#

        embedding_vector = OpenAIEmbeddings().embed_query(question1)
        embedding_vecton1 = OpenAIEmbeddings().embed_query(question2)

        # Search the DB.
        results = db.similarity_search_by_vector(embedding_vector, k=9)
        results2 = db2.similarity_search_by_vector(embedding_vecton1, k=9)

        # -----------------------formatting data-----------------------------------#

        dict = {"hotels": [], "restaurants": []}
        for i in range(len(results)):
            dict["hotels"].append(results[i].page_content)

        for i in range(len(results2)):
            dict["restaurants"].append(results2[i].page_content)
        structured_data = {"hotels": [], "restaurant": []}

        for i in dict["hotels"]:
            parts = i.split("\n")
            if len(parts) > 4:

                # Extract relevant information
                nom = parts[1]
                ville = parts[0]
                adresse = parts[3]
                numero_telephone = parts[4]

                # Construct a dictionary for the entry
                entry_dict = {
                    "nom": nom,
                    "ville": ville,
                    "adresse": adresse,
                    "numero_telephone": numero_telephone,
                }
                structured_data["hotels"].append(entry_dict)
        for i in dict["restaurants"]:

            parts = i.split()

            # Extracting restaurant name
            name = " ".join(parts[:-5])

            # Extracting rating
            rating = parts[-5]

            # Extracting location
            location = parts[-4]

            # Extracting city
            city = parts[-3]

            # Extracting address
            address = " ".join(parts[-2:])

            # Extracting phone number
            phone_number = parts[-6]

            # Construct restaurant dictionary
            restaurant = {
                "name": name,
                "rating": rating,
                "location": location,
                "city": city,
                "address": address,
                "phone_number": phone_number,
            }
            structured_data["restaurant"].append(restaurant)

        # -----------------------use OpenAI MODELS --------------------#

        chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.3)

        data = {
            "hotels": [
                {
                    "nom": "ETOILE DU NORD",
                    "ville": "Tanger",
                    "adresse": "11, Bd. Sidi med.Ben Abdellah",
                    "numero_telephone": "0539-33-65-76/77",
                },
                {
                    "nom": "ROYAL",
                    "ville": "Tanger",
                    "adresse": "144, Rue de la Plage Salah Eddin Elayoubi",
                    "numero_telephone": "0539/93.89.68 064/16.78.80",
                },
            ],
            "restaurants": [
                {
                    "nom": "Le Pecheur de Detroit",
                    "type": "1 fourchette",
                    "provinence": "Tanger-Tétouan-Al Hoceima",
                    "region": "Tanger-Assilah",
                    "ville": "TANGER",
                    "adresse": "RUE AHMED CHAOUKI/ TANGER",
                    "numero_telephone": "539373810",
                }
            ],
            "activites": [
                {
                    "nom": "Visite de la Kasbah des Oudayas",
                    "prix": "Gratuit (certains sites peuvent avoir des frais d'entrée)",
                },
                {"nom": "Promenade le long de la corniche", "prix": "Gratuit"},
                {"nom": "Visite du Musée de la Kasbah", "prix": "50 MAD par adulte"},
                {"nom": "Shopping au souk", "prix": "Variable en fonction des achats"},
                {"nom": "Détente sur les plages de Tanger", "prix": "Gratuit"},
                {
                    "nom": "Visite du Musée d'Art Contemporain de la Ville de Tanger (MACVT)",
                    "prix": "30 MAD par personne",
                },
                {
                    "nom": "Excursion à Cap Spartel et les grottes d'Hercule",
                    "prix": "200 MAD par personne (inclut le transport et le guide)",
                },
                {
                    "nom": "Dégustation de fruits de mer",
                    "prix": "Variable en fonction du restaurant",
                },
                {
                    "nom": "Excursion à Chefchaouen",
                    "prix": "Variable en fonction du type de visite guidée",
                },
                {
                    "nom": "Exploration de la Médina de Tanger",
                    "prix": "Gratuit (certains sites peuvent avoir des frais d'entrée)",
                },
            ],
            "food": [
                "Tagine (variety of flavors)",
                "Couscous (traditional Moroccan dish)",
                "Mint Tea (popular Moroccan beverage)",
                "Seafood (fresh from the coast)",
                "Paella (Spanish influence)",
                "Tapas (Spanish influence)",
            ],
        }
        messages = [
            SystemMessage(
                content=f"""
Act as a travel recommendation. You should absolutely utilize the data provided by users for hotels and restaurants. All hotels in the provided data should be included in the template. For the activites and food, generate them with the maximum informations (for example 20 activity and 10 food to do) based on your knowledge. and strictly adhere to the provided template {data}  don't add now fields .all the subfield on the json file should be on the ville {ville1} if  a ville not in {ville1} should not be in the output for example the template contain only TANGER on ville .
"""
            ),
            HumanMessage(
                content=f"By using the whole {structured_data} format it to json  . i will be there with {nombre} member,generate me some activities to do and food to eat to do in {ville1} from your knowledge .the objectif of this travel is {objectif} "
            ),
        ]
        response = chat(messages)

        traject = Traject.objects.create(
            userId=user_id,
            budget=budget,
            ville=ville1,
            time=time,
            person_number=nombre,
            json_content=response.content,  # Python dictionary to be serialized into JSON
        )

        return Response(json.loads(response.content))


class TrajectPlanification(APIView):
    def get(self, request):
        token = request.COOKIES.get("jwt")
        if not token:
            raise AuthenticationFailed("Unauthenticated!")

        try:
            payload = jwt.decode(token, "secret", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Unauthenticated!")
        user_id = payload["id"]
        traject = Traject.objects.filter(userId=user_id).last()
        time = traject.time
        ville = traject.ville
        number = traject.person_number
        chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.3)
        data = {
            "day1": {
                "activities": [
                    {
                        "name": "Visit Medina",
                        "type": "Sightseeing",
                        "location": "Medina, Tanger",
                        "description": "Explore the historic Medina of Tanger",
                        "price": "Free",
                    },
                    {
                        "name": "Explore Kasbah",
                        "type": "Sightseeing",
                        "location": "Kasbah, Tanger",
                        "description": "Discover the ancient Kasbah of Tanger",
                        "price": "$5",
                    },
                    {
                        "name": "Shopping in Souk",
                        "type": "Shopping",
                        "location": "Souk, Tanger",
                        "description": "Experience the vibrant Souk markets of Tanger",
                        "price": "Varies",
                    },
                ],
                "food": ["Try Tagine", "Taste Couscous", "Enjoy Mint Tea"],
                "transportation": "Local taxis or walking",
            },
            "day2": {
                "activities": [
                    {
                        "name": "Visit Hercules Cave",
                        "type": "Sightseeing",
                        "location": "Hercules Cave, Tanger",
                        "description": "Explore the mythical Hercules Cave",
                        "price": "$10",
                    },
                    {
                        "name": "Relax on the Beach",
                        "type": "Leisure",
                        "location": "Beaches, Tanger",
                        "description": "Enjoy a relaxing day on the beautiful beaches",
                        "price": "Free",
                    },
                    {
                        "name": "Explore Cape Spartel",
                        "type": "Sightseeing",
                        "location": "Cape Spartel, Tanger",
                        "description": "Discover the scenic Cape Spartel",
                        "price": "Free",
                    },
                ],
                "food": ["Fresh seafood", "Paella", "Tapas"],
                "transportation": "Local buses or rental car",
            },
            "day3": {
                "activities": [
                    {
                        "name": "Explore Tangier American Legation Museum",
                        "type": "Museum",
                        "location": "Tangier American Legation Museum, Tanger",
                        "description": "Visit the historic Tangier American Legation Museum",
                        "price": "$8",
                    },
                    {
                        "name": "Visit Gran Teatro Cervantes",
                        "type": "Theatre",
                        "location": "Gran Teatro Cervantes, Tanger",
                        "description": "Experience cultural performances at Gran Teatro Cervantes",
                        "price": "$6",
                    },
                    {
                        "name": "Relax in Petit Socco",
                        "type": "Leisure",
                        "location": "Petit Socco, Tanger",
                        "description": "Relax and people-watch in Petit Socco",
                        "price": "Varies",
                    },
                ],
                "food": ["Try Bocadillos", "Spanish Omelette", "Churros"],
                "transportation": "Walking or local buses",
            },
        }

        messages = [
            SystemMessage(
                content=f"""
Act as a travel recommendation.the journees, you should generate it based on your knowledge, adjusting the length according to the number of days the user will spend there, and strictly adhere to the provided template :
{data}
"""
            ),
            HumanMessage(
                content=f"give me a planning for activities i will spend {time} in {ville} i will be there with {number} member"
            ),
        ]
        response = chat(messages)

        plan = Plan.objects.create(userId=user_id, json_content=response.content)

        return Response(json.loads(response.content))


class GetMatchs(ListAPIView):
    queryset = (
        Match.objects.all()
    )  # Assurez-vous que cette requête récupère les objets Match que vous souhaitez sérialiser
    serializer_class = MatchSerializer


class GetOneMatch(RetrieveAPIView):
    queryset = (
        Match.objects.all()
    )  # Assurez-vous que cette requête récupère les objets Match que vous souhaitez sérialiser
    serializer_class = MatchSerializer


class GetGuides(ListAPIView):
    queryset = Guider.objects.all()
    serializer_class = GuideSerializer


class GetOneGuide(RetrieveAPIView):
    queryset = (
        Match.objects.all()
    )  # Assurez-vous que cette requête récupère les objets Match que vous souhaitez sérialiser
    serializer_class = MatchSerializer
