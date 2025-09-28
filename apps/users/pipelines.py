def check_profile_completion(user=None, *args, **kwargs):
    """Pipeline personnalisé pour vérifier l'achèvement du profil après social auth"""
    if user:
        required_fields = ['telephone', 'adresse', 'nom', 'prenom']
        missing_fields = [field for field in required_fields if not getattr(user, field)]
        
        if missing_fields:
            user.profile_completed = False
        else:
            user.profile_completed = True
        user.save()
    
    return {'user': user}