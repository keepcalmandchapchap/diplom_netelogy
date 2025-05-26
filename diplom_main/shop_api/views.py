from django.shortcuts import render
from django.http import Http404
from django.contrib.auth import authenticate
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTTokenUserAuthentication, JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status

from .serializers import RegisterSerializer, UserInfoSerializer, LoginSerializer, PositionSerializer
from .models import User, UserInfo, Position
from .permissions import IsUserOrStaff, IsInGroups, IsUserOrInGroup


def gen_error(serializer, error_status: status): 
    if not serializer.is_valid():
            return Response(
                {
                    'status': 'error',
                    'errors': serializer.errors,
            }, status=error_status
            )


class RegisterView(APIView):
    '''
    Представление для регистрации стандартного пользователя
    '''
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            reposnse_data = {'user': serializer.data}
            headers = {
                'Authorization': f'Bearer {access_token}',
                'X-Refresh-Token': refresh_token
            }

            return Response(reposnse_data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class LoginView(APIView):
    '''
    Вью для входа
    '''
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})

        gen_error(serializer, status.HTTP_401_UNAUTHORIZED)
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        response_data = {
            'status': 'success'
        }
        headers = {
                'Authorization': f'Bearer {str(refresh.access_token)}',
                'X-Refresh-Token': str(refresh)
        }
        return Response(response_data, headers=headers, status=status.HTTP_200_OK)
        

# class UserInfoView(ModelViewSet):
#     queryset = UserInfo.objects.all()
#     serializer_class = UserInfoSerializer
#     permission_classes = [IsAuthenticated, IsUserOrStaff]
#     filter_backends = [DjangoFilterBackend, SearchFilter]
#     filterset_fields = ['user']
#     search_fields = ['user']

#     def get_queryset(self):

#         queryset = super().get_queryset()
#         if not self.request.user.is_staff:
#             queryset = queryset.filter(user=self.request.user.id)

#         return queryset
    
#     @action(detail=False, methods=['patch'])
#     def change_phone(self, request):

#         phone_target = self.queryset.get(user=self.request.user.id, type_info='phone')
#         if phone_target and self.request.data.get('phone'):
#             phone_target.value_info = self.request.data['phone']
#             phone_target.save()
#             return Response({'status': 'access'}, status=status.HTTP_205_RESET_CONTENT)
#         return Response({'status': 'error'}, self.serializer_class.errors)


class UserInfoViewForOwner(APIView):
    authentication_classes = [JWTTokenUserAuthentication]
    permission_classes = [IsAuthenticated]
       
    def get_objects(self, re   quest):
        return UserInfo.objects.filter(user=request.user)

    def get_object(self, request):
        try:
            return UserInfo.objects.get(user=request.user)
        except UserInfo.DoesNotExist:
            return None

    def post(self, request):
        serializer = UserInfoSerializer(data=request.data) 
        error_response = gen_error(serializer, status.HTTP_400_BAD_REQUEST)
        if error_response:
            return error_response
        serializer.save()
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def put(self, request, pk):
        instance = self.get_object(pk)
        if not instance:
            return Response({'status': 'error', 'message': 'Объект не найден'}, status=status.HTTP_404_NOT_FOUND)
    
        serializer = UserInfoSerializer(instance, data=request.data)
        error_response = gen_error(serializer, status.HTTP_400_BAD_REQUEST)
        if error_response:
            return error_response
        serializer.save(user=request.user)
        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
    
    def patch(self, request, pk):
        instance = self.get_object(pk)
        if not instance:
            return Response({'status': 'error', 'message': 'Объект не найден'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserInfoSerializer(instance, data=request.data, partial=True)
        error_response = gen_error(serializer, status.HTTP_400_BAD_REQUEST)
        if error_response:
            return error_response

        serializer.save(user=request.user)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        instance = self.get_object(pk)
        if not instance:
            return Response({'status': 'error', 'message': 'Объект не найден'}, status=status.HTTP_404_NOT_FOUND)

        instance.delete(user=request.user)
        return Response({
            'status': 'success',
            'message': 'Объект успешно удален'
        }, status=status.HTTP_204_NO_CONTENT)


class PositionView(ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsInGroups(['employee_base', 'manager_base'])]
        if self.request.method in ['POST', 'PUT', 'DELETE']:
            return [IsInGroups(['manager_base'])]
        return super().get_permissions()
    