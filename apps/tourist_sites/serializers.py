from rest_framework import serializers
from apps.tourist_sites.models import TouristSite, TouristSiteCategory, TouristSiteImage


class TouristSiteCategorySerializer(serializers.ModelSerializer):
    """Sérialiseur pour les catégories de sites touristiques"""
    
    class Meta:
        model = TouristSiteCategory
        fields = ['id', 'name', 'description']


class TouristSiteImageSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les images de sites touristiques"""
    
    class Meta:
        model = TouristSiteImage
        fields = ['id', 'image', 'caption', 'is_primary', 'uploaded_at']


class TouristSiteSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les sites touristiques"""
    
    category = TouristSiteCategorySerializer(read_only=True)
    images = TouristSiteImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = TouristSite
        fields = [
            'id', 'name', 'description', 'category', 'latitude', 'longitude',
            'is_active', 'created_at', 'updated_at', 'images'
        ]


class TouristSiteListSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la liste des sites touristiques (version simplifiée)"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = TouristSite
        fields = [
            'id', 'name', 'description', 'category_name', 'latitude', 'longitude',
            'is_active', 'created_at', 'primary_image'
        ]
    
    def get_primary_image(self, obj):
        """Récupère l'image principale du site"""
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return {
                'id': primary_image.id,
                'image': primary_image.image.url,
                'caption': primary_image.caption
            }
        return None


class TouristSiteCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour créer un site touristique"""
    
    class Meta:
        model = TouristSite
        fields = ['name', 'description', 'category', 'latitude', 'longitude', 'is_active']
    
    def validate_latitude(self, value):
        """Validation de la latitude"""
        if value < -90 or value > 90:
            raise serializers.ValidationError("La latitude doit être comprise entre -90 et 90.")
        return value
    
    def validate_longitude(self, value):
        """Validation de la longitude"""
        if value < -180 or value > 180:
            raise serializers.ValidationError("La longitude doit être comprise entre -180 et 180.")
        return value


class TouristSiteUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour mettre à jour un site touristique"""
    
    class Meta:
        model = TouristSite
        fields = ['name', 'description', 'category', 'latitude', 'longitude', 'is_active']
        extra_kwargs = {
            'name': {'required': False},
            'description': {'required': False},
            'category': {'required': False},
            'latitude': {'required': False},
            'longitude': {'required': False},
            'is_active': {'required': False},
        }


class TouristSiteMapSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la carte des sites touristiques"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = TouristSite
        fields = ['id', 'name', 'description', 'category_name', 'latitude', 'longitude'] 