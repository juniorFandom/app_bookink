from rest_framework import serializers
from .models import Tour, TourDestination, TourDestinationImage, TourBooking, TourSchedule, TourReview


class TourDestinationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourDestinationImage
        fields = '__all__'


class TourDestinationSerializer(serializers.ModelSerializer):
    images = TourDestinationImageSerializer(many=True, read_only=True)
    class Meta:
        model = TourDestination
        fields = '__all__'


class TourSerializer(serializers.ModelSerializer):
    destinations = TourDestinationSerializer(many=True, read_only=True)
    class Meta:
        model = Tour
        fields = '__all__'


class TourDetailSerializer(serializers.ModelSerializer):
    destinations = TourDestinationSerializer(many=True, read_only=True)
    class Meta:
        model = Tour
        fields = '__all__'


class TourImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourDestinationImage
        fields = '__all__'


class TourBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourBooking
        fields = '__all__'


class TourScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourSchedule
        fields = '__all__'


class TourReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourReview
        fields = '__all__' 