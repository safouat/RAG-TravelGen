# urls.py
from django.urls import path
from .views import (
    TrajectDetail,
    TrajectPlanification,
    GetOneUserTraject,
    GetUserPlannings,
    GetUserTrajects,
    RegisterView,
    LoginView,
    LogoutView,
    UserInfo,
    GetMatchs,
    GetOneMatch,
    GetGuides,
    GetOneGuide,
    GetPlanTraject,
    SendGuideMail,
    GetCityTransport,
    
)


urlpatterns = [
    path("Register/", RegisterView.as_view(), name="register"),
    path("Login/", LoginView.as_view(), name="login"),
    path("Lougout/", LogoutView.as_view(), name="logout"),
    path("UserInfo/", UserInfo.as_view(), name="UserInfo"),
    path("Traject/", TrajectDetail.as_view(), name="traject_detail"),
    path("Trajects/", GetUserTrajects.as_view(), name="trajects"),
    path("OneTraject", GetOneUserTraject.as_view(), name="traject1"),
    path("Plan/", TrajectPlanification.as_view(), name="traject_plan"),
    path("Plans/", GetUserPlannings.as_view(), name="traject_plan"),
    path("Matchs/", GetMatchs.as_view(), name="Matchs"),
    path("match/<int:pk>/", GetOneMatch.as_view(), name="get_one_match"),
    path("Guides/", GetGuides.as_view(), name="Guides"),
    path("guide/<int:pk>/", GetOneGuide.as_view(), name="get_one_guide"),
    path("PlanTraject/", GetPlanTraject.as_view(), name="traject_plan1"),
    path("Mail/", SendGuideMail.as_view(), name="send_mail"),
    path("Transport/", GetCityTransport.as_view(), name="send_mail"),
    


]
