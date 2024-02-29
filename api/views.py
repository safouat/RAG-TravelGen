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
from .serializer import (
    GuideSerializer,
    MatchSerializer,
    UserSerializer,
    TrajectSerializer,
    PlanSerializer,
)

CHROMA_PATH = "./api/data/chroma"
CHROMA_PATH2 = "./api/data/chroma2"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM")

chat = ChatOpenAI(api_key=OPENAI_API_KEY, model_name="gpt-3.5-turbo", temperature=0.3)


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

        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        response = Response()
        response["Authorization"] = f"Bearer {token}"
        response.data = {"jwt": token}
        return response


class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "success"})
        response.delete_header("Authorization")
        return response


class UserInfo(APIView):
    def get(self, request):
        authorization_header = request.headers.get("Authorization")

        if not authorization_header or "Bearer " not in authorization_header:
            raise AuthenticationFailed("Unauthenticated!")

        token = authorization_header.split(" ")[1]

        if not token:
            raise AuthenticationFailed("Unauthenticated!")

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Unauthenticated!")

        user = User.objects.filter(id=payload["id"]).first()

        if user is None:
            raise AuthenticationFailed("User not found!")

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

        token = request.headers.get("Authorization").split(" ")[1]
        if not token:
            raise AuthenticationFailed("Unauthenticated!")

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
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
            "description": """
            Tanger, a city pulsating with history and flavor, beckons travelers with its myriad experiences. Immerse yourself in its enchanting streets where the past intertwines with the present. Stay at the iconic ETOILE DU NORD or the luxurious ROYAL hotels, offering comfort and elegance amidst Tanger's charm. Indulge your taste buds at Le Pecheur de Detroit, where culinary mastery meets the freshest seafood delights.
            Explore the heart of Tanger through a myriad of activities. Wander through the ancient Kasbah des Oudayas, a testament to the city's rich heritage. Take in the breathtaking views from Cap Spartel and delve into the mysteries of the caves of Hercules on a captivating excursion. Discover contemporary art at the Museum of Contemporary Art of Tanger (MACVT) or lose yourself in the vibrant souks, where every corner holds a treasure waiting to be found.
            Savor the essence of Moroccan cuisine with aromatic Tagines, delicate Couscous, and refreshing Mint Tea. Tantalize your palate with the fusion of Spanish influence in Paella and Tapas. Treat yourself to a gastronomic journey through the flavors of Tanger's diverse culinary landscape.
            Whether you're exploring the winding streets of the Medina or basking in the sun-kissed beaches, Tanger offers an unforgettable blend of history, culture, and gastronomy that promises to enchant every traveler who sets foot on its shores.""",
            "title": "Tanger Travel Guide",
        }

        messages = [
            SystemMessage(
                content=f"""
            Act as a travel recommendation.
            You should absolutely utilize the data provided by users for hotels and restaurants.
            All hotels in the provided data should be included in the template.
            For the activites and food, generate them with the maximum informations (for example 20 activity and 10 food to do) based on your knowledge.
            and strictly adhere to the provided template {data}  don't add now fields .all the subfield on the json file should be on the ville {ville1} if  a ville not in {ville1} should not be in the output for example the template contain only TANGER on ville. 
            For the description it should include all hotels and retaurants given by user for activities talk a little bit about them. 
            For the title you should generate it yourself.
        """
            ),
            HumanMessage(
                content=f"By using the whole {structured_data} format it to json  . i will be there with {nombre} member,generate me some activities to do and food to eat to do in {ville1} from your knowledge .for activities generate them based on objectif of this travel is {objectif} "
            ),
        ]
        response = chat(messages)

        json_content = json.loads(response.content)

        traject = Traject.objects.create(
            userId=user_id,
            budget=budget,
            ville=ville1,
            time=time,
            person_number=nombre,
            json_content=json_content,
            description=json_content["description"],
            title=json_content["title"],
        )

        return Response({"id": traject.id, "json_content": json_content})


class GetPlanTraject(APIView):
    def get(self, request):
        trajectId = request.GET.get("trajectId")
        plan = Plan.objects.filter(traject=trajectId)
        serializer = PlanSerializer(plan, many=True)

        return Response(serializer.data)


class GetUserTrajects(APIView):
    def get(self, request):
        token = request.headers.get("Authorization").split(" ")[1]
        if not token:
            raise AuthenticationFailed("Unauthenticated!")

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Unauthenticated!")

        user_id = payload["id"]

        # Récupération des trajects de l'utilisateur avec l'ID user_id
        trajects = Traject.objects.filter(userId=user_id).all()

        # Sérialisation des trajects récupérés
        serializer = TrajectSerializer(trajects, many=True)

        return Response(serializer.data)


class GetOneUserTraject(APIView):
    def get(self, request):
        id = request.GET.get("id")

        token = request.headers.get("Authorization").split(" ")[1]
        if not token:
            raise AuthenticationFailed("Unauthenticated!")

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Unauthenticated!")

        user_id = payload["id"]
        trajects = Traject.objects.filter(userId=user_id, id=id).all()
        serializer = TrajectSerializer(trajects, many=True)
        return Response(serializer.data)


class TrajectPlanification(APIView):
    def get(self, request):
        token = request.headers.get("Authorization").split(" ")[1]
        if not token:
            raise AuthenticationFailed("Unauthenticated!")

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Unauthenticated!")
        user_id = payload["id"]
        traject = Traject.objects.filter(userId=user_id).last()
        time = traject.time
        ville = traject.ville
        number = traject.person_number
        trajectId = Traject.objects.get(id=traject.id)
        # -----------------------use OpenAI MODELS --------------------#
        # fmt: off
        data = {
            "day1": {
                "activities": [
                    {
                        "name": "Visit Jardin Majorelle",
                        "type": "Sightseeing",
                        "location": "Jardin Majorelle, Marrakech",
                        "description": "Explore the beautiful gardens of Jardin Majorelle",
                        "price": "$10"
                    },
                    {
                        "name": "Explore Medina",
                        "type": "Sightseeing",
                        "location": "Medina, Marrakech",
                        "description": "Get lost in the bustling streets of the historic Medina",
                        "price": "Free"
                    },
                    {
                        "name": "Shop in Souks",
                        "type": "Shopping",
                        "location": "Souks, Marrakech",
                        "description": "Experience the vibrant souks of Marrakech",
                        "price": "Varies"
                    }
                ],
                "food": ["Try Tagine", "Taste Moroccan Tea", "Enjoy Couscous"],
                "transportation": "Local taxis or walking"
            },
            "day2": {
                "activities": [
                    {
                        "name": "Visit Bahia Palace",
                        "type": "Sightseeing",
                        "location": "Bahia Palace, Marrakech",
                        "description": "Discover the grandeur of Bahia Palace",
                        "price": "$7"
                    },
                    {
                        "name": "Explore Jemaa el-Fnaa",
                        "type": "Sightseeing",
                        "location": "Jemaa el-Fnaa, Marrakech",
                        "description": "Experience the lively square of Jemaa el-Fnaa",
                        "price": "Free"
                    },
                    {
                        "name": "Relax in Hammam",
                        "type": "Leisure",
                        "location": "Hammam, Marrakech",
                        "description": "Indulge in a traditional Moroccan hammam experience",
                        "price": "$20"
                    }
                ],
                "food": [
                    "Try Pastilla",
                    "Savor Moroccan Pastries",
                    "Enjoy Harira Soup"
                ],
                "transportation": "Local buses or rental car"
            }
        }
        data = json.dumps(data)
        messages = [
            SystemMessage(
                content=f"""
            Act as a travel recommendation. 
            the journees, you should generate it based on your knowledge, adjusting the length according to the number of days the user will spend there, 
            and strictly adhere to the provided template: {data}, THE OUTPUT MUST BE A VALID JSON.
            """
            ),
            HumanMessage(
                content=f"""give me a planning for activities to do while my {time} stay at {ville},I will be there with {number} member,
                  and I want to do some activities and eat some food, and i want to know how to move from one place to another"""
            ),
        ]
        response = chat(messages)

        plan = Plan.objects.create(userId=user_id, json_content=response.content, traject=trajectId)
        return Response(json.loads(response.content))


class GetUserPlannings(APIView):
    def get(self, request):
        token = request.headers.get("Authorization").split(" ")[1]
        if not token:
            raise AuthenticationFailed("Unauthenticated!")

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Unauthenticated!")

        user_id = payload["id"]

        # Récupération des trajects de l'utilisateur avec l'ID user_id
        trajects = Plan.objects.filter(userId=user_id).all()

        # Sérialisation des trajects récupérés
        serializer = PlanSerializer(trajects, many=True)

        return Response(serializer.data)


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
