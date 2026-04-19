from rest_framework.response import Response
from rest_framework.views import APIView


class RiskEngineView(APIView):
    def get(self, request):
        return Response({'success': True, 'message': 'Risk engine endpoint'})
