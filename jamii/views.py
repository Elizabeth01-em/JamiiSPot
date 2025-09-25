






# register app to get apikey
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])  # Only logged-in users can register apps
# def register_app(request):
#     serializer = APIKeySerializer(data=request.data)
#     if serializer.is_valid():
#         api_key = APIKey.objects.create(
#             app_name=serializer.validated_data["app_name"],
#             owner=request.user
#         )
#         return Response({
#             "client_id": api_key.client_id,
#             "client_secret": api_key.client_secret
#         }, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# # get access token for the app   
# @api_view(['POST'])
# def get_access_token(request):
#     client_id = request.data.get("client_id")
#     client_secret = request.data.get("client_secret")

#     try:
#         api_key = APIKey.objects.get(client_id=client_id, client_secret=client_secret)
#     except APIKey.DoesNotExist:
#         return Response({"error": "Invalid API credentials"}, status=401)

#     # Generate JWT Tokens
#     refresh = RefreshToken.for_user(api_key.owner)
#     return Response({
#         "access_token": str(refresh.access_token),
#         "refresh_token": str(refresh),
#         "expires_in": 1800  # 30 min
#     })

