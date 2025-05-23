from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CreateUserView, AnalysisViewSet, S3TestView, VideoUploadTestView, VideoViewSet, S3SignedURLView, S3ImageProxyView, S3ObjectExistsView, ChangePasswordView, DeleteAccountView, UserInfoView, DeepFakeDetectionView, ForgotPasswordView, ResetPasswordView, TestEmailView

router = DefaultRouter()
router.register(r'analysis', AnalysisViewSet, basename='analysis')
router.register(r'videos', VideoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('signup/', CreateUserView.as_view(), name='create_user'),
    path('users/create/', CreateUserView.as_view(), name='user-create'),
    path('detect/', AnalysisViewSet.as_view({'post': 'create'}), name='detect'),
    
    # Account Management Endpoints
    path('user/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('user/delete-account/', DeleteAccountView.as_view(), name='delete-account'),
    path('user/info/', UserInfoView.as_view(), name='user-info'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('test-email/', TestEmailView.as_view(), name='test-email'),
    
    # S3 testing routes
    path('test/s3/', S3TestView.as_view(), name='test_s3_connection'),
    path('test/upload/', VideoUploadTestView.as_view(), name='test_video_upload'),
    
    # S3 utilities
    path('s3/signed-url/', S3SignedURLView.as_view(), name='s3_signed_url'),
    path('s3/object-exists/', S3ObjectExistsView.as_view(), name='s3_object_exists'),
    
    # Image proxy
    path('proxy-image/', S3ImageProxyView.as_view(), name='proxy_image'),
    
    # Deepfake detection
    path('detect-deepfake/', DeepFakeDetectionView.as_view(), name='detect_deepfake'),
    
    # Specific endpoint for deepfake API (for external integrations)
    path('api/deepfake/', DeepFakeDetectionView.as_view(), name='deepfake_api'),
    
    # Analyze existing video (by ID)
    path('video/<int:video_id>/analyze/', DeepFakeDetectionView.as_view(), name='analyze_video'),
]


'''from django.urls import path
from . import views
from .views import UnapprovedOperatorsView, AuthorizeOperatorView,UserDetailView, RejectOperatorView, AllAuthorizedOperatorsView, CreateParkingSpotsMapView, ParkingSpotsMapView, FlipParkingSpotStatusView2, FlipParkingSpotStatusView,ParkingSpotsView, ForgotPasswordView, ResetPasswordView, UnapprovedMapsView, AllAuthorizedMapsView, RejectMapView,AuthorizeMapView, UpdatePhoneNumberView, OrganizationsView, CreateMapReportView, GetMapReportsView, DeleteMapReportView

urlpatterns = [
    path("notes/", views.NoteListCreate.as_view(), name="note-list"),
    path("notes/delete/<int:pk>/", views.NoteDelete.as_view(), name="delete-note"),
    path('operators/unapproved/', UnapprovedOperatorsView.as_view(), name='unapproved_operators'),
    path('operators/authorized/', AllAuthorizedOperatorsView.as_view(), name='all_authorized_operators'),
    path('operators/<int:operator_id>/authorize/', AuthorizeOperatorView.as_view(), name='authorize_operator'),
    path('operators/<int:operator_id>/Reject/', RejectOperatorView.as_view(), name='reject_operator'),
    path('user/', UserDetailView.as_view(), name='user_detail'),
    path('create-parking-map/', CreateParkingSpotsMapView.as_view(), name='create_parking_map'),
    path('parking-map/<int:operator_id>/', ParkingSpotsMapView.as_view(), name='view_parking_map'),
    path('parking-spot/<int:pk>/flip-status2/', FlipParkingSpotStatusView2.as_view(), name='flip_parking_spot_status'),
    path('parking-map/<int:map_id>/spots/', ParkingSpotsView.as_view(), name='parking_spots_map'),
    path('parking-spot/<int:spot_id>/flip-status/', FlipParkingSpotStatusView.as_view(), name='flip_parking_spot_status'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('maps/unapproved/', UnapprovedMapsView.as_view(), name='unapproved_maps'),
    path('maps/authorized/', AllAuthorizedMapsView.as_view(), name='all_authorized_maps'),
    path('map/<int:map_id>/authorize/', AuthorizeMapView.as_view(), name='authorize_map'),
    path('map/<int:map_id>/Reject/', RejectMapView.as_view(), name='reject_map'),
    path('update-phone/', UpdatePhoneNumberView.as_view(), name='update_phone'),
   # path('organizations/', OrganizationsView.as_view(), name='organizations'),
   path('organizations/', OrganizationsView.as_view(), name='organizations'),
   path('map-report/', CreateMapReportView.as_view(), name='create_map_report'),
   path('map-reports/<int:map_id>/', GetMapReportsView.as_view(), name='get_map_reports'),
   path('map-report/<int:report_id>/', DeleteMapReportView.as_view(), name='delete_map_report'),

]
'''
