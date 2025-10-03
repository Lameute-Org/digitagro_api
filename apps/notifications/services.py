# ==================== apps/notifications/services.py ====================
from .models import Notification
from typing import Dict, Optional, List


# ==================== NOTIFICATION TYPES ====================
class NotificationType:
    """Constants for notification types"""
    NEW_ORDER = 'new_order'
    PAYMENT_RECEIVED = 'payment_received'
    PRODUCT_SHIPPED = 'product_shipped'
    NEW_REVIEW = 'new_review'
    NEW_MESSAGE = 'new_message'
    TRANSFORMATION_REQUEST = 'transformation_request'
    TRANSFORMATION_COMPLETED = 'transformation_completed'
    TRANSPORT_STARTED = 'transport_started'
    TRANSPORT_REQUEST = 'transport_request'
    TRANSPORT_CONFIRMED = 'transport_confirmed'
    TRANSPORT_ARRIVED = 'transport_arrived'
    DELIVERY_COMPLETED = 'delivery_completed'
    DELIVERY_DELAYED = 'delivery_delayed'
    BULK_ORDER = 'bulk_order'
    PRODUCTS_READY = 'products_ready'
    ORDER_CONFIRMED = 'order_confirmed'
    STOCK_UPDATED = 'stock_updated'
    NEW_DEVICE = 'new_device'
    PASSWORD_CHANGED = 'password_changed'
    PROFILE_INCOMPLETE = 'profile_incomplete'
    ORDER_CANCELLED = 'order_cancelled'
    REFUND_REQUESTED = 'refund_requested'


# ==================== COMMON STRINGS ====================
class NotificationText:
    """Constants for commonly used strings"""
    # Titles
    TITLE_NEW_MESSAGE = 'Nouveau message'
    TITLE_NEW_ORDER = 'Nouvelle commande reçue'
    TITLE_PAYMENT_RECEIVED = 'Paiement reçu'
    TITLE_NEW_REVIEW = 'Nouvelle évaluation'
    TITLE_ORDER_CONFIRMED = 'Commande confirmée'
    TITLE_DELIVERY_COMPLETED = 'Livraison effectuée'
    TITLE_PRODUCT_SHIPPED = 'Produit expédié'
    TITLE_TRANSFORMATION_COMPLETED = 'Transformation terminée'
    
    # Common field names
    FIELD_AMOUNT = 'amount'
    FIELD_RATING = 'rating'
    
    # Currency
    CURRENCY_FCFA = 'FCFA'


class NotificationService:
    """Service centralisé pour TOUTES les notifications"""
    
    @staticmethod
    def create(
        recipient,
        notif_type: str,
        title: str,
        message: str,
        content_object=None,
        data: Optional[Dict] = None
    ) -> Notification:
        notif_data = {
            'recipient': recipient,
            'type': notif_type,
            'title': title,
            'message': message,
            'data': data or {}
        }
        
        if content_object:
            from django.contrib.contenttypes.models import ContentType
            notif_data['content_type'] = ContentType.objects.get_for_model(content_object)
            notif_data['object_id'] = content_object.id
        
        return Notification.objects.create(**notif_data)
    
    @staticmethod
    def bulk_create(notifications_data: List[Dict]) -> List[Notification]:
        return Notification.objects.bulk_create([
            Notification(**data) for data in notifications_data
        ])
    
    # ==================== PRODUCTEUR ====================
    
    @staticmethod
    def notify_producteur_new_order(commande):
        """Nouvelle commande reçue"""
        return NotificationService.create(
            recipient=commande.production.producteur.user,
            notif_type=NotificationType.NEW_ORDER,
            title=NotificationText.TITLE_NEW_ORDER,
            message=f'{commande.client.get_full_name()} - {commande.quantite} {commande.production.produit}',
            content_object=commande,
            data={'order_id': commande.id, NotificationText.FIELD_AMOUNT: float(commande.montant_total)}
        )
    
    @staticmethod
    def notify_producteur_payment(commande):
        """Paiement reçu"""
        return NotificationService.create(
            recipient=commande.production.producteur.user,
            notif_type=NotificationType.PAYMENT_RECEIVED,
            title=NotificationText.TITLE_PAYMENT_RECEIVED,
            message=f'{commande.montant_total} {NotificationText.CURRENCY_FCFA} reçu',
            content_object=commande,
            data={NotificationText.FIELD_AMOUNT: float(commande.montant_total)}
        )
    
    @staticmethod
    def notify_producteur_shipment_confirmed(commande):
        """Confirmation d'expédition"""
        return NotificationService.create(
            recipient=commande.production.producteur.user,
            notif_type=NotificationType.PRODUCT_SHIPPED,
            title='Expédition confirmée',
            message=f'Commande #{commande.id} expédiée',
            content_object=commande
        )
    
    @staticmethod
    def notify_producteur_review(evaluation):
        """Nouvelle évaluation"""
        return NotificationService.create(
            recipient=evaluation.producteur.user,
            notif_type=NotificationType.NEW_REVIEW,
            title=NotificationText.TITLE_NEW_REVIEW,
            message=f'{evaluation.note}/5 - {evaluation.commentaire[:50]}',
            content_object=evaluation,
            data={NotificationText.FIELD_RATING: evaluation.note}
        )
    
    @staticmethod
    def notify_producteur_message(message):
        """Nouveau message acheteur"""
        return NotificationService.create(
            recipient=message.destinataire,
            notif_type=NotificationType.NEW_MESSAGE,
            title=NotificationText.TITLE_NEW_MESSAGE,
            message=f'{message.expediteur.get_full_name()}: {message.contenu[:50]}',
            content_object=message
        )
    
    @staticmethod
    def notify_producteur_transformation_status(demande_transformation, accepted):
        """Transformation acceptée/refusée"""
        return NotificationService.create(
            recipient=demande_transformation.producteur.user,
            notif_type=NotificationType.TRANSFORMATION_REQUEST,
            title='Transformation ' + ('acceptée' if accepted else 'refusée'),
            message=f'Demande transformation {demande_transformation.type_transformation}',
            content_object=demande_transformation,
            data={'accepted': accepted}
        )
    
    @staticmethod
    def notify_producteur_products_ready(transformation):
        """Produits transformés prêts"""
        return NotificationService.create(
            recipient=transformation.producteur.user,
            notif_type=NotificationType.TRANSFORMATION_COMPLETED,
            title='Produits transformés prêts',
            message=f'Transformation {transformation.type_transformation} terminée',
            content_object=transformation
        )
    
    @staticmethod
    def notify_producteur_transformer_payment(paiement):
        """Paiement transformateur reçu"""
        return NotificationService.create(
            recipient=paiement.producteur.user,
            notif_type=NotificationType.PAYMENT_RECEIVED,
            title='Paiement transformateur reçu',
            message=f'{paiement.montant} {NotificationText.CURRENCY_FCFA} reçu',
            content_object=paiement,
            data={NotificationText.FIELD_AMOUNT: float(paiement.montant)}
        )
    
    @staticmethod
    def notify_producteur_transport_scheduled(transport):
        """Transport programmé"""
        return NotificationService.create(
            recipient=transport.commande.production.producteur.user,
            notif_type=NotificationType.TRANSPORT_STARTED,
            title='Transport programmé',
            message=f'Livraison vers {transport.destination}',
            content_object=transport
        )
    
    @staticmethod
    def notify_producteur_delivery_completed(transport):
        """Livraison effectuée"""
        return NotificationService.create(
            recipient=transport.commande.production.producteur.user,
            notif_type=NotificationType.DELIVERY_COMPLETED,
            title=NotificationText.TITLE_DELIVERY_COMPLETED,
            message=f'Commande #{transport.commande.id} livrée',
            content_object=transport
        )
    
    @staticmethod
    def notify_producteur_price_negotiation(negociation):
        """Négociation prix B2B"""
        return NotificationService.create(
            recipient=negociation.production.producteur.user,
            notif_type=NotificationType.BULK_ORDER,
            title='Négociation prix initiée',
            message=f'Distributeur: {negociation.distributeur.user.get_full_name()}',
            content_object=negociation
        )
    
    @staticmethod
    def notify_producteur_bulk_order(commande_b2b):
        """Commande grossiste confirmée"""
        return NotificationService.create(
            recipient=commande_b2b.production.producteur.user,
            notif_type=NotificationType.BULK_ORDER,
            title='Commande en gros confirmée',
            message=f'{commande_b2b.quantite} unités - {commande_b2b.montant_total} {NotificationText.CURRENCY_FCFA}',
            content_object=commande_b2b,
            data={NotificationText.FIELD_AMOUNT: float(commande_b2b.montant_total)}
        )
    
    # ==================== TRANSPORTEUR ====================
    
    @staticmethod
    def notify_transporteur_new_request(reservation):
        """Nouvelle demande réservation"""
        return NotificationService.create(
            recipient=reservation.service_transport.transporteur.user,
            notif_type=NotificationType.TRANSPORT_REQUEST,
            title='Nouvelle demande transport',
            message=f'{reservation.origine} → {reservation.destination}',
            content_object=reservation
        )
    
    @staticmethod
    def notify_transporteur_reservation_confirmed(reservation):
        """Réservation confirmée"""
        return NotificationService.create(
            recipient=reservation.service_transport.transporteur.user,
            notif_type=NotificationType.TRANSPORT_CONFIRMED,
            title='Réservation confirmée',
            message=f'Client: {reservation.client.get_full_name()}',
            content_object=reservation
        )
    
    @staticmethod
    def notify_transporteur_payment(paiement):
        """Paiement reçu"""
        return NotificationService.create(
            recipient=paiement.transporteur.user,
            notif_type=NotificationType.PAYMENT_RECEIVED,
            title=NotificationText.TITLE_PAYMENT_RECEIVED,
            message=f'{paiement.montant} {NotificationText.CURRENCY_FCFA} - {paiement.type_paiement}',
            content_object=paiement,
            data={NotificationText.FIELD_AMOUNT: float(paiement.montant), 'type': paiement.type_paiement}
        )
    
    @staticmethod
    def notify_transporteur_start_requested(trajet):
        """Début trajet demandé"""
        return NotificationService.create(
            recipient=trajet.transporteur.user,
            notif_type=NotificationType.TRANSPORT_STARTED,
            title='Début trajet demandé',
            message=f'Départ prévu: {trajet.heure_depart}',
            content_object=trajet
        )
    
    @staticmethod
    def notify_transporteur_delivery_confirmed(livraison):
        """Livraison confirmée destinataire"""
        return NotificationService.create(
            recipient=livraison.transporteur.user,
            notif_type=NotificationType.DELIVERY_COMPLETED,
            title='Livraison confirmée',
            message=f'Destinataire: {livraison.destinataire.get_full_name()}',
            content_object=livraison
        )
    
    @staticmethod
    def notify_transporteur_review(evaluation):
        """Nouvelle évaluation"""
        return NotificationService.create(
            recipient=evaluation.transporteur.user,
            notif_type=NotificationType.NEW_REVIEW,
            title=NotificationText.TITLE_NEW_REVIEW,
            message=f'{evaluation.note}/5 - {evaluation.commentaire[:50]}',
            content_object=evaluation,
            data={NotificationText.FIELD_RATING: evaluation.note}
        )
    
    @staticmethod
    def notify_transporteur_message(message):
        """Nouveau message client"""
        return NotificationService.create(
            recipient=message.destinataire,
            notif_type=NotificationType.NEW_MESSAGE,
            title=NotificationText.TITLE_NEW_MESSAGE,
            message=f'{message.expediteur.get_full_name()}: {message.contenu[:50]}',
            content_object=message
        )
    
    # ==================== TRANSFORMATEUR ====================
    
    @staticmethod
    def notify_transformateur_new_request(demande):
        """Nouvelle demande transformation"""
        return NotificationService.create(
            recipient=demande.transformateur.user,
            notif_type=NotificationType.TRANSFORMATION_REQUEST,
            title='Nouvelle demande',
            message=f'{demande.type_transformation} - {demande.quantite}kg',
            content_object=demande
        )
    
    @staticmethod
    def notify_transformateur_advance_payment(paiement):
        """Avance reçue"""
        return NotificationService.create(
            recipient=paiement.transformateur.user,
            notif_type=NotificationType.PAYMENT_RECEIVED,
            title='Avance reçue',
            message=f'{paiement.montant} {NotificationText.CURRENCY_FCFA}',
            content_object=paiement,
            data={NotificationText.FIELD_AMOUNT: float(paiement.montant)}
        )
    
    @staticmethod
    def notify_transformateur_products_received(reception):
        """Produits bruts reçus"""
        return NotificationService.create(
            recipient=reception.transformateur.user,
            notif_type=NotificationType.PRODUCTS_READY,
            title='Produits bruts reçus',
            message=f'{reception.quantite}kg - {reception.type_produit}',
            content_object=reception
        )
    
    @staticmethod
    def notify_transformateur_transformation_completed(transformation):
        """Transformation terminée"""
        return NotificationService.create(
            recipient=transformation.transformateur.user,
            notif_type=NotificationType.TRANSFORMATION_COMPLETED,
            title=NotificationText.TITLE_TRANSFORMATION_COMPLETED,
            message='Produits prêts à livrer',
            content_object=transformation
        )
    
    @staticmethod
    def notify_transformateur_final_payment(paiement):
        """Paiement final"""
        return NotificationService.create(
            recipient=paiement.transformateur.user,
            notif_type=NotificationType.PAYMENT_RECEIVED,
            title='Paiement final reçu',
            message=f'{paiement.montant} {NotificationText.CURRENCY_FCFA}',
            content_object=paiement,
            data={NotificationText.FIELD_AMOUNT: float(paiement.montant)}
        )
    
    @staticmethod
    def notify_transformateur_review(evaluation):
        """Nouvelle évaluation"""
        return NotificationService.create(
            recipient=evaluation.transformateur.user,
            notif_type=NotificationType.NEW_REVIEW,
            title=NotificationText.TITLE_NEW_REVIEW,
            message=f'{evaluation.note}/5',
            content_object=evaluation,
            data={NotificationText.FIELD_RATING: evaluation.note}
        )
    
    @staticmethod
    def notify_transformateur_message(message):
        """Nouveau message"""
        return NotificationService.create(
            recipient=message.destinataire,
            notif_type=NotificationType.NEW_MESSAGE,
            title=NotificationText.TITLE_NEW_MESSAGE,
            message=f'{message.expediteur.get_full_name()}: {message.contenu[:50]}',
            content_object=message
        )
    
    # ==================== DISTRIBUTEUR ====================
    
    @staticmethod
    def notify_distributeur_order_confirmed(commande_b2b):
        """Commande confirmée producteur"""
        return NotificationService.create(
            recipient=commande_b2b.distributeur.user,
            notif_type=NotificationType.ORDER_CONFIRMED,
            title=NotificationText.TITLE_ORDER_CONFIRMED,
            message=f'{commande_b2b.production.produit} - {commande_b2b.quantite}',
            content_object=commande_b2b
        )
    
    @staticmethod
    def notify_distributeur_payment_processed(paiement):
        """Paiement traité"""
        return NotificationService.create(
            recipient=paiement.distributeur.user,
            notif_type=NotificationType.PAYMENT_RECEIVED,
            title='Paiement traité',
            message=f'{paiement.montant} {NotificationText.CURRENCY_FCFA}',
            content_object=paiement,
            data={NotificationText.FIELD_AMOUNT: float(paiement.montant)}
        )
    
    @staticmethod
    def notify_distributeur_delivery_in_progress(livraison):
        """Livraison en cours"""
        return NotificationService.create(
            recipient=livraison.distributeur.user,
            notif_type=NotificationType.PRODUCT_SHIPPED,
            title='Livraison en cours',
            message=f'Transporteur: {livraison.transporteur.user.get_full_name()}',
            content_object=livraison
        )
    
    @staticmethod
    def notify_distributeur_goods_received(reception):
        """Marchandise reçue"""
        return NotificationService.create(
            recipient=reception.distributeur.user,
            notif_type=NotificationType.STOCK_UPDATED,
            title='Marchandise reçue',
            message='Stock mis à jour',
            content_object=reception
        )
    
    @staticmethod
    def notify_distributeur_message(message):
        """Nouveau message producteur"""
        return NotificationService.create(
            recipient=message.destinataire,
            notif_type=NotificationType.NEW_MESSAGE,
            title=NotificationText.TITLE_NEW_MESSAGE,
            message=f'{message.expediteur.get_full_name()}: {message.contenu[:50]}',
            content_object=message
        )
    
    @staticmethod
    def notify_distributeur_consumer_order(commande):
        """Nouvelle commande consommateur"""
        return NotificationService.create(
            recipient=commande.distributeur.user,
            notif_type=NotificationType.NEW_ORDER,
            title='Nouvelle commande',
            message=f'{commande.consommateur.get_full_name()} - {commande.montant_total} {NotificationText.CURRENCY_FCFA}',
            content_object=commande,
            data={NotificationText.FIELD_AMOUNT: float(commande.montant_total)}
        )
    
    @staticmethod
    def notify_distributeur_consumer_payment(paiement):
        """Paiement consommateur reçu"""
        return NotificationService.create(
            recipient=paiement.distributeur.user,
            notif_type=NotificationType.PAYMENT_RECEIVED,
            title='Paiement consommateur',
            message=f'{paiement.montant} {NotificationText.CURRENCY_FCFA}',
            content_object=paiement,
            data={NotificationText.FIELD_AMOUNT: float(paiement.montant)}
        )
    
    # ==================== CONSOMMATEUR ====================
    
    @staticmethod
    def notify_consommateur_new_production(production, consommateur):
        """Nouvelle production disponible (selon préférences)"""
        return NotificationService.create(
            recipient=consommateur,
            notif_type=NotificationType.NEW_ORDER,
            title='Nouvelle production',
            message=f'{production.produit} disponible - {production.prix_unitaire} {NotificationText.CURRENCY_FCFA}',
            content_object=production
        )
    
    @staticmethod
    def notify_consommateur_order_confirmed(commande):
        """Commande confirmée"""
        return NotificationService.create(
            recipient=commande.consommateur,
            notif_type=NotificationType.ORDER_CONFIRMED,
            title=NotificationText.TITLE_ORDER_CONFIRMED,
            message=f'Commande #{commande.id} confirmée',
            content_object=commande
        )
    
    @staticmethod
    def notify_consommateur_payment_validated(paiement):
        """Paiement validé"""
        return NotificationService.create(
            recipient=paiement.consommateur,
            notif_type=NotificationType.PAYMENT_RECEIVED,
            title='Paiement validé',
            message=f'{paiement.montant} {NotificationText.CURRENCY_FCFA}',
            content_object=paiement,
            data={NotificationText.FIELD_AMOUNT: float(paiement.montant)}
        )
    
    @staticmethod
    def notify_consommateur_product_shipped(expedition):
        """Produit expédié"""
        return NotificationService.create(
            recipient=expedition.commande.consommateur,
            notif_type=NotificationType.PRODUCT_SHIPPED,
            title=NotificationText.TITLE_PRODUCT_SHIPPED,
            message=f'Commande #{expedition.commande.id}',
            content_object=expedition
        )
    
    @staticmethod
    def notify_consommateur_delivery_in_progress(livraison):
        """Livraison en cours"""
        return NotificationService.create(
            recipient=livraison.destinataire,
            notif_type=NotificationType.PRODUCT_SHIPPED,
            title='Livraison en cours',
            message=f'Transporteur: {livraison.transporteur.user.get_full_name()}',
            content_object=livraison
        )
    
    @staticmethod
    def notify_consommateur_delivery_completed(livraison):
        """Livraison effectuée"""
        return NotificationService.create(
            recipient=livraison.destinataire,
            notif_type=NotificationType.DELIVERY_COMPLETED,
            title=NotificationText.TITLE_DELIVERY_COMPLETED,
            message='Votre commande est arrivée',
            content_object=livraison
        )
    
    @staticmethod
    def notify_consommateur_message(message):
        """Message producteur/transporteur"""
        return NotificationService.create(
            recipient=message.destinataire,
            notif_type=NotificationType.NEW_MESSAGE,
            title=NotificationText.TITLE_NEW_MESSAGE,
            message=f'{message.expediteur.get_full_name()}: {message.contenu[:50]}',
            content_object=message
        )
    
    @staticmethod
    def notify_consommateur_transport_reserved(reservation):
        """Transport réservé"""
        return NotificationService.create(
            recipient=reservation.client,
            notif_type=NotificationType.TRANSPORT_CONFIRMED,
            title='Transport réservé',
            message=f'{reservation.origine} → {reservation.destination}',
            content_object=reservation
        )
    
    @staticmethod
    def notify_consommateur_transport_position(position):
        """Mise à jour position (temps réel - géré par WebSocket séparé)"""
        return NotificationService.create(
            recipient=position.client,
            notif_type=NotificationType.TRANSPORT_STARTED,
            title='Position mise à jour',
            message=f'Lat: {position.latitude}, Lng: {position.longitude}',
            content_object=position
        )
    
    @staticmethod
    def notify_consommateur_arrival_imminent(transport):
        """Arrivée imminente"""
        return NotificationService.create(
            recipient=transport.client,
            notif_type=NotificationType.TRANSPORT_ARRIVED,
            title='Arrivée imminente',
            message='Le transporteur arrive dans 10 minutes',
            content_object=transport
        )
    
    @staticmethod
    def notify_consommateur_transport_arrived(transport):
        """Transport arrivé"""
        return NotificationService.create(
            recipient=transport.client,
            notif_type=NotificationType.TRANSPORT_ARRIVED,
            title='Transport arrivé',
            message='Votre livraison est arrivée',
            content_object=transport
        )
    
    @staticmethod
    def notify_consommateur_product_available_distributor(produit):
        """Produit disponible distributeur"""
        return NotificationService.create(
            recipient=produit.consommateur,
            notif_type=NotificationType.NEW_ORDER,
            title='Produit disponible',
            message=f'{produit.nom} chez {produit.distributeur.user.get_full_name()}',
            content_object=produit
        )
    
    @staticmethod
    def notify_consommateur_distributor_order_confirmed(commande):
        """Commande distributeur confirmée"""
        return NotificationService.create(
            recipient=commande.consommateur,
            notif_type=NotificationType.ORDER_CONFIRMED,
            title=NotificationText.TITLE_ORDER_CONFIRMED,
            message=f'Distributeur: {commande.distributeur.user.get_full_name()}',
            content_object=commande
        )
    
    # ==================== TRANSVERSAL (TOUS) ====================
    
    @staticmethod
    def notify_new_device_login(user, device_info):
        """Connexion nouvel appareil"""
        return NotificationService.create(
            recipient=user,
            notif_type=NotificationType.NEW_DEVICE,
            title='Nouvelle connexion',
            message=f'Connexion depuis {device_info.get("device", "appareil inconnu")}',
            data=device_info
        )
    
    @staticmethod
    def notify_password_changed(user):
        """Mot de passe modifié"""
        return NotificationService.create(
            recipient=user,
            notif_type=NotificationType.PASSWORD_CHANGED,
            title='Mot de passe modifié',
            message='Votre mot de passe a été changé'
        )
    
    @staticmethod
    def notify_suspicious_login(user, attempt_info):
        """Tentative connexion suspecte"""
        return NotificationService.create(
            recipient=user,
            notif_type=NotificationType.NEW_DEVICE,
            title='Connexion suspecte',
            message=f'Tentative depuis {attempt_info.get("ip", "IP inconnue")}',
            data=attempt_info
        )
    
    @staticmethod
    def notify_profile_incomplete(user):
        """Profil incomplet"""
        return NotificationService.create(
            recipient=user,
            notif_type=NotificationType.PROFILE_INCOMPLETE,
            title='Profil incomplet',
            message='Veuillez compléter votre profil'
        )
    
    @staticmethod
    def notify_payment_method_added(user, method_name):
        """Nouveau moyen paiement"""
        return NotificationService.create(
            recipient=user,
            notif_type=NotificationType.PAYMENT_RECEIVED,
            title='Moyen de paiement ajouté',
            message=f'{method_name} configuré',
            data={'method': method_name}
        )
    
    @staticmethod
    def notify_message_read(message):
        """Message lu"""
        return NotificationService.create(
            recipient=message.expediteur,
            notif_type=NotificationType.NEW_MESSAGE,
            title='Message lu',
            message=f'{message.destinataire.get_full_name()} a lu votre message',
            content_object=message
        )
    
    @staticmethod
    def notify_review_reminder(user, target_user, role):
        """Rappel évaluation"""
        return NotificationService.create(
            recipient=user,
            notif_type=NotificationType.NEW_REVIEW,
            title='Évaluation en attente',
            message=f'Évaluez {target_user.get_full_name()} ({role})',
            data={'target_user_id': target_user.id, 'role': role}
        )
    
    @staticmethod
    def notify_review_published(evaluation):
        """Évaluation publiée"""
        return NotificationService.create(
            recipient=evaluation.auteur,
            notif_type=NotificationType.NEW_REVIEW,
            title='Évaluation publiée',
            message=f'Votre note: {evaluation.note}/5',
            content_object=evaluation
        )
    
    # ==================== ANOMALIES/URGENCES ====================
    
    @staticmethod
    def notify_delivery_delayed(livraison, delay_minutes):
        """Retard livraison"""
        return NotificationService.create(
            recipient=livraison.destinataire,
            notif_type=NotificationType.DELIVERY_DELAYED,
            title='Retard de livraison',
            message=f'Retard estimé: {delay_minutes} minutes',
            content_object=livraison,
            data={'delay': delay_minutes}
        )
    
    @staticmethod
    def notify_gps_interrupted(transport):
        """GPS interrompu"""
        return NotificationService.create(
            recipient=transport.client,
            notif_type=NotificationType.DELIVERY_DELAYED,
            title='Géolocalisation interrompue',
            message='Suivi GPS temporairement indisponible',
            content_object=transport
        )
    
    @staticmethod
    def notify_order_unconfirmed_24h(commande):
        """Commande non confirmée 24h"""
        return NotificationService.create(
            recipient=commande.production.producteur.user,
            notif_type=NotificationType.DELIVERY_DELAYED,
            title='Commande en attente',
            message=f'Commande #{commande.id} non confirmée depuis 24h',
            content_object=commande
        )
    
    @staticmethod
    def notify_payment_pending(paiement):
        """Paiement en attente"""
        return NotificationService.create(
            recipient=paiement.beneficiaire,
            notif_type=NotificationType.PAYMENT_RECEIVED,
            title='Paiement en attente',
            message=f'{paiement.montant} {NotificationText.CURRENCY_FCFA} en validation',
            content_object=paiement,
            data={NotificationText.FIELD_AMOUNT: float(paiement.montant)}
        )
    
    @staticmethod
    def notify_order_cancelled(commande, cancelled_by):
        """Annulation commande"""
        recipients = [commande.production.producteur.user, commande.consommateur]
        return [
            NotificationService.create(
                recipient=user,
                notif_type=NotificationType.ORDER_CANCELLED,
                title='Commande annulée',
                message=f'Annulée par {cancelled_by.get_full_name()}',
                content_object=commande
            ) for user in recipients if user != cancelled_by
        ]
    
    @staticmethod
    def notify_refund_requested(remboursement):
        """Demande remboursement"""
        return NotificationService.create(
            recipient=remboursement.vendeur,
            notif_type=NotificationType.REFUND_REQUESTED,
            title='Demande de remboursement',
            message=f'{remboursement.montant} {NotificationText.CURRENCY_FCFA} - Motif: {remboursement.motif}',
            content_object=remboursement,
            data={NotificationText.FIELD_AMOUNT: float(remboursement.montant)}
        )