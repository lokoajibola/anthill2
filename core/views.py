from django.shortcuts import render

def homepage(request):
    subscription_plans = [
        {
            'name': 'Basic',
            'price': '$99/month',
            'features': ['Up to 500 students', 'Basic analytics', 'Email support']
        },
        {
            'name': 'Pro',
            'price': '$199/month',
            'features': ['Up to 2000 students', 'Advanced analytics', 'Priority support']
        },
        {
            'name': 'Enterprise',
            'price': '$399/month',
            'features': ['Unlimited students', 'Full analytics', '24/7 support']
        }
    ]
    return render(request, 'core/homepage.html', {'plans': subscription_plans})

def contact_us(request):
    return render(request, 'core/contact.html')