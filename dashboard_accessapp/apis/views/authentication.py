from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from dashboard_accessapp.apis.serializers.authentication import AdminLoginSerializer


class AdminLoginView(CreateAPIView):
    permission_classes = []  # public

    def post(self, request, *args, **kwargs):
        serializer = AdminLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)