"""
Management command to seed the Coderr database with realistic demo data.

Usage:
    python manage.py seed_demo_data
    python manage.py seed_demo_data --flush   # wipe existing demo data first

This creates a handful of business users with offers (each with basic /
standard / premium tiers), a few customer users, some orders, and some
reviews — enough for the marketplace to look populated for a portfolio demo.

All demo users share the password: demo1234
"""
import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from auth_app.models import Profile
from coderr_app.models import CoderrProfile, Offer, OfferDetail, Order, Review

DEMO_PASSWORD = "demo1234"

BUSINESSES = [
    {   "username": "dev_anna",
        "first_name": "Anna",
        "last_name": "Müller",
        "location": "Berlin, Germany",
        "description": (
            "Full stack developer with a background in biology and data science. "
            "Specializing in Python, Django, REST APIs, and Docker deployments."
		 ),
        "offers": [
            {
                "title": "Custom Django Backend Development",
                "description": "I'll build a robust, well-tested Django backend for your project — REST API, auth, database design, and deployment-ready setup.",
                "tiers": [
                    ("Basic", 150, 5, 1, ["Single endpoint", "Basic tests"]),
                    ("Standard", 400, 10, 3, ["Full CRUD API", "Auth included", "Unit tests"]),
                    ("Premium", 900, 14, 999, ["Full backend", "Docker + deployment setup", "Docs", "Unlimited revisions"]),
                ],
            },
            {
                "title": "Biomedical Image Analysis Pipeline",
                "description": "I'll build a PyTorch-based image analysis or segmentation pipeline (e.g. U-Net) for microscopy or biomedical imaging data, from raw images to trained model.",
                "tiers": [
                    ("Basic", 300, 7, 1, ["Preprocessing + existing model inference"]),
                    ("Standard", 700, 14, 2, ["Custom model training", "Evaluation report"]),
                    ("Premium", 1400, 21, 999, ["Full pipeline", "Fine-tuning support", "Documentation", "Handover session"]),
                ],
            },
            {
                "title": "Code Review & Refactoring (Python/Django)",
                "description": "Get a thorough review of your Python/Django codebase with actionable, prioritized refactoring suggestions.",
                "tiers": [
                    ("Basic", 60, 3, 1, ["Up to 500 lines reviewed"]),
                    ("Standard", 120, 5, 2, ["Up to 2000 lines", "Refactor suggestions"]),
                    ("Premium", 250, 7, 999, ["Full codebase review", "Pairing session", "Follow-up"]),
                ],
            },
        ],
    },
]

CUSTOMERS = [
    {"username": "startup_founder_max", "first_name": "Max", "last_name": "Bauer", "location": "Hamburg, Germany"},
    {"username": "sarah_builds", "first_name": "Sarah", "last_name": "Jenkins", "location": "London, UK"},
    {"username": "indie_hacker_tom", "first_name": "Tom", "last_name": "Weber", "location": "Vienna, Austria"},
]

REVIEW_TEXTS = [
    "Great communication and delivered exactly what was promised. Would hire again.",
    "Very professional, fast turnaround, and the code quality was excellent.",
    "Solid work overall, a few small revisions needed but handled quickly.",
    "Exceeded expectations — clear documentation and clean implementation.",
    "Good experience, responsive and easy to work with throughout the project.",
]


class Command(BaseCommand):
    help = "Seed the database with demo businesses, offers, orders, and reviews."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete previously seeded demo users (and their data) before seeding again.",
        )

    def handle(self, *args, **options):
        all_usernames = [b["username"] for b in BUSINESSES] + [c["username"] for c in CUSTOMERS]

        if options["flush"]:
            demo_profiles = Profile.objects.filter(user__username__in=all_usernames)
            Review.objects.filter(business_user__in=demo_profiles).delete()
            Review.objects.filter(reviewer__in=demo_profiles).delete()
            Order.objects.filter(customer_user__in=demo_profiles).delete()
            Order.objects.filter(business_user__in=demo_profiles).delete()
            OfferDetail.objects.filter(offer__profile__in=demo_profiles).delete()
            Offer.objects.filter(profile__in=demo_profiles).delete()
            deleted, _ = User.objects.filter(username__in=all_usernames).delete()
            self.stdout.write(self.style.WARNING(f"Flushed existing demo data ({deleted} related rows removed)."))

        with transaction.atomic():
            business_profiles = [self._create_person(b, "business") for b in BUSINESSES]
            customer_profiles = [self._create_person(c, "customer") for c in CUSTOMERS]

            if Offer.objects.filter(profile__in=business_profiles).exists():
                self.stdout.write(self.style.WARNING(
                    "Demo offers already exist for these businesses — skipping offer/order/review "
                    "creation to avoid duplicates. Run with --flush first if you want to reseed."
                ))
                self.stdout.write(self.style.SUCCESS(
                    f"\nDone (no changes). All demo accounts use the password: {DEMO_PASSWORD}"
                ))
                return

            all_offer_details = []
            for biz_data, profile in zip(BUSINESSES, business_profiles):
                for offer_data in biz_data["offers"]:
                    offer = Offer.objects.create(
                        profile=profile,
                        title=offer_data["title"],
                        description=offer_data["description"],
                    )
                    for name, price, delivery_days, revisions, features in offer_data["tiers"]:
                        detail = OfferDetail.objects.create(
                            offer=offer,
                            title=name,
                            revisions=revisions,
                            delivery_time_in_days=delivery_days,
                            price=price,
                            features=features,
                            offer_type=name.lower(),
                        )
                        all_offer_details.append((detail, profile))
                    self.stdout.write(f"  Created offer: {offer.title} ({len(offer_data['tiers'])} tiers)")

            statuses = ["completed", "completed", "in_progress", "completed", "cancelled"]
            sample_orders = random.sample(all_offer_details, k=min(6, len(all_offer_details)))
            created_orders = []
            for i, (detail, biz_profile) in enumerate(sample_orders):
                customer_profile = customer_profiles[i % len(customer_profiles)]
                order = Order.objects.create(
                    offer=detail.offer,
                    offer_detail=detail,
                    customer_user=customer_profile,
                    business_user=biz_profile,
                    title=detail.title,
                    revisions=detail.revisions,
                    delivery_time_in_days=detail.delivery_time_in_days,
                    price=detail.price,
                    features=detail.features,
                    offer_type=detail.offer_type,
                    status=statuses[i % len(statuses)],
                )
                created_orders.append(order)
            self.stdout.write(f"  Created {len(created_orders)} orders")
            seen_pairs = set()
            review_count = 0
            for order in created_orders:
                if order.status != "completed":
                    continue
                pair = (order.customer_user_id, order.business_user_id)
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                Review.objects.create(
                    business_user=order.business_user,
                    reviewer=order.customer_user,
                    description=random.choice(REVIEW_TEXTS),
                    rating=random.randint(4, 5),
                )
                review_count += 1
            self.stdout.write(f"  Created {review_count} reviews")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Seeded {len(business_profiles)} businesses, {len(customer_profiles)} customers.\n"
            f"All demo accounts use the password: {DEMO_PASSWORD}"
        ))

    def _create_person(self, data, profile_type):
        user, created = User.objects.get_or_create(
            username=data["username"],
            defaults={
                "email": f"{data['username']}@example.com",
                "first_name": data["first_name"],
                "last_name": data["last_name"],
            },
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()

        profile, _ = Profile.objects.get_or_create(user=user, defaults={"type": profile_type})
        if profile.type != profile_type:
            profile.type = profile_type
            profile.save()

        CoderrProfile.objects.get_or_create(
            profile=profile,
            defaults={
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "location": data["location"],
                "description": data.get("description", ""),
                "working_hours": "Mon-Fri, 9am-5pm",
            },
        )
        return profile
