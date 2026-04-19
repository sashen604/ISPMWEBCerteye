from rest_framework.response import Response
from rest_framework.views import APIView


class AlertsView(APIView):
    def get(self, request):
        return Response({'success': True, 'message': 'Alerts endpoint'})
