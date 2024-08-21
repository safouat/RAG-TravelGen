import argparse
from dataclasses import dataclass
from langchain.vectorstores.chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings,OpenAI
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)




import os

CHROMA_PATH = "chroma"
CHROMA_PATH2 = "chroma2"



os.environ['OPENAI_API_KEY'] = '|'










def main():
    


    # Prepare the DB.
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    db2 = Chroma(persist_directory=CHROMA_PATH2, embedding_function=embedding_function)


    budget=700 
    ville1="ChefChaoun"
    time="3 days"



    #-------------helping the search models with those statistics-----------------------#
    hebergement=budget*0.5
    restaurant=budget*0.3
    if 30<restaurant < 150:
       rest="1 fourchette"
    elif 150 <= restaurant < 300:
        rest="2 fourchette"

    else:
        rest="3 fourchette"
    

    if (100 <= hebergement < 150):
       hotel = "1 étoile"
    elif (150 <= hebergement < 250):
       hotel = "2 étoiles"
    elif (250 <= hebergement < 700):
       hotel = "3 étoiles"
    elif (700 <= hebergement < 800):
       hotel = "4 étoiles"
    else:
      hotel = "5 étoiles"
    #---------------------------------------------------------------#
    
   
    #-------------------------questions-----------------------------#

    question1=f"give me  hotels in {ville1} and those hotels should be with {hotel} "
    question2=f"find all  {ville1} "


    #-------------------------embedding Models-----------------------#


    embedding_vector = OpenAIEmbeddings().embed_query(question1)
    embedding_vecton1 = OpenAIEmbeddings().embed_query(question2)

    # Search the DB.
    results = db.similarity_search_by_vector(embedding_vector,k=9)
    results2 = db2.similarity_search_by_vector(embedding_vecton1,k=9)

    #-----------------------formatting data-----------------------------------#


    dict={"hotels":[],"restaurants":[]}
    for i in range(len(results)):
          dict["hotels"].append(results[i].page_content)
  
    for i in range(len(results2)):
          dict["restaurants"].append(results2[i].page_content)
    structured_data = {"hotels":[],"restaurant":[]}

    for i in dict["hotels"]:
        parts = i.split('\n')
        if(len(parts)>4):
        
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
            "numero_telephone": numero_telephone
        }
          structured_data["hotels"].append(entry_dict)
    for i in dict["restaurants"]:
        
        parts = i.split()

    # Extracting restaurant name
        name = ' '.join(parts[:-5])

    # Extracting rating
        rating = parts[-5]

    # Extracting location
        location = parts[-4]

    # Extracting city
        city = parts[-3]

    # Extracting address
        address = ' '.join(parts[-2:])

    # Extracting phone number
        phone_number = parts[-6]

    # Construct restaurant dictionary
        restaurant = {
        "name": name,
        "rating": rating,
        "location": location,
        "city": city,
        "address": address,
        "phone_number": phone_number
    }
        structured_data["restaurant"].append(restaurant)


    #-----------------------use OpenAI MODELS --------------------#


    chat = ChatOpenAI(model_name="gpt-3.5-turbo",temperature=0.3)
     #-----------------------Fine Tuning --------------------#

    data={
  "hotels": [
    {
      "nom": "ETOILE DU NORD",
      "ville": "Tanger",
      "adresse": "11, Bd. Sidi med.Ben Abdellah",
      "numero_telephone": "0539-33-65-76/77"
    },
    {
      "nom": "ROYAL",
      "ville": "Tanger",
      "adresse": "144, Rue de la Plage Salah Eddin Elayoubi",
      "numero_telephone": "0539/93.89.68 064/16.78.80"
    }
  ],
  "restaurants": [
    {
      "nom": "Le Pecheur de Detroit",
      "type": "1 fourchette",
      "provinence": "Tanger-Tétouan-Al Hoceima",
      "region": "Tanger-Assilah",
      "ville": "TANGER",
      "adresse": "RUE AHMED CHAOUKI/ TANGER",
      "numero_telephone": "539373810"
    }
  ],
  
  "activites": [
    {
      "nom": "Visite de la Kasbah des Oudayas",
      "prix": "Gratuit (certains sites peuvent avoir des frais d'entrée)"
    },
    {
      "nom": "Promenade le long de la corniche",
      "prix": "Gratuit"
    },
    {
      "nom": "Visite du Musée de la Kasbah",
      "prix": "50 MAD par adulte"
    },
    {
      "nom": "Shopping au souk",
      "prix": "Variable en fonction des achats"
    },
    {
      "nom": "Détente sur les plages de Tanger",
      "prix": "Gratuit"
    },
    {
      "nom": "Visite du Musée d'Art Contemporain de la Ville de Tanger (MACVT)",
      "prix": "30 MAD par personne"
    },
    {
      "nom": "Excursion à Cap Spartel et les grottes d'Hercule",
      "prix": "200 MAD par personne (inclut le transport et le guide)"
    },
    {
      "nom": "Dégustation de fruits de mer",
      "prix": "Variable en fonction du restaurant"
    },
    {
      "nom": "Excursion à Chefchaouen",
      "prix": "Variable en fonction du type de visite guidée"
    },
    {
      "nom": "Exploration de la Médina de Tanger",
      "prix": "Gratuit (certains sites peuvent avoir des frais d'entrée)"
    }
  ],
  "food": [
    "Tagine (variety of flavors)",
    "Couscous (traditional Moroccan dish)",
    "Mint Tea (popular Moroccan beverage)",
    "Seafood (fresh from the coast)",
    "Paella (Spanish influence)",
    "Tapas (Spanish influence)"
  ]
}
    messages = [
    SystemMessage(content=f"""
Act as a travel recommendation. You should absolutely utilize the data provided by users for hotels and restaurants. All hotels in the provided data should be included in the template. For the activites and food, generate them with the maximum informations (for example 20 activity and 10 food to do) based on your knowledge. and strictly adhere to the provided template {data}  don't add now fields .all the subfield on the json file should be on the city {ville1} if  a ville not in {ville1} should not be in the output for example the template contain only TANGER on ville .
"""),
    HumanMessage(content=f"By using the whole {structured_data} format it to json  . generate me some activities to do and food to eat to do in {ville1} from your knowledge ")
]
    response=chat(messages)
    print(response.content,end='\n')


if __name__ == "__main__":
    main()
