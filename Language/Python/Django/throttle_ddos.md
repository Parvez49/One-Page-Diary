## DDoS Attack
    A DDoS (Distributed Denial of Service) attack is a malicious attempt to disrupt the normal traffic of a targeted server, service, or network by overwhelming it with a flood of internet traffic from multiple sources. 
    Unlike a DoS (Denial of Service) attack, which comes from a single source, a DDoS attack uses thousands or millions of compromised devices (botnets) to launch a coordinated attack.

The server gets overloaded, consuming all available:

  - Bandwidth (network saturation)
  - CPU/Memory (resource exhaustion)
  - Database connections (application layer attacks)

### Django REST Framework Rate Limiting
```
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',  # for anonymous users
        'user': '1000/hour',  # for authenticated users
        'login': '20/hour',   # special limit for login attempts
        'payment': '30/minute' # payment processing
    }
}

# views.py
from rest_framework.throttling import ScopedRateThrottle

class LoginView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'
    
    def post(self, request):
        # login logic
        pass

class PaymentView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'payment'
    
    def post(self, request):
        # payment processing logic
        pass
```

Note:  If we set Throttle in settings.py, all views will apply the default throttle rates for both anonymous and authenticated users. If a view does not require these throttle classes, you must manually override them by setting: throttle_classes = []
