from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from models import FrequentlyBoughtTogether, UserProductView
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
from config import settings
from collections import Counter
import logging

logger = logging.getLogger(__name__)

async def get_collaborative_filtering_recommendations(product_id: int, db: AsyncSession):
    """
    Finds users who viewed the given product and recommends other products
    they also viewed. (Customers Who Viewed This Also Viewed)
    """
    # Find users who viewed the target product
    query1 = select(UserProductView.user_id).filter(UserProductView.product_id == product_id)
    result1 = await db.execute(query1)
    users_who_viewed_product = [row[0] for row in result1.all()]

    if not users_who_viewed_product:
        return []

    # Find all other products these users have viewed
    query2 = select(UserProductView.product_id).filter(
        UserProductView.user_id.in_(users_who_viewed_product)
    ).filter(
        UserProductView.product_id != product_id
    )
    result2 = await db.execute(query2)
    other_viewed_products = [row[0] for row in result2.all()]

    # Count the occurrences of each product
    product_counts = Counter(other_viewed_products)

    # Get the most common products, ordered by frequency
    recommended_product_ids = [pid for pid, _ in product_counts.most_common(10)]
    return recommended_product_ids

async def update_content_based_recommendations(db: AsyncSession):
    """
    Calculates product similarity based on text description.
    """
    # Fetch all products from Catalog Service (via HTTP since it's decoupled)
    catalog_url = getattr(settings, 'CATALOG_SERVICE_INTERNAL_URL', 'http://catalog_service:8002/internal/products/bulk-lookup/')
    try:
        # We might need an endpoint in catalog to just fetch all active products for ML training
        # For now, let's assume there's a GET /internal/products/all/
        resp = requests.get('http://catalog_service:8002/internal/products/all/', timeout=10)
        if resp.status_code != 200:
            logger.error("Failed to fetch products from catalog service.")
            return
        products = resp.json()
    except Exception as e:
        logger.error(f"Error connecting to catalog service: {e}")
        return

    if len(products) < 2:
        return

    # Create a corpus of text
    product_texts = [f"{p.get('ProductName', '')} {p.get('ProductDescription', '')}" for p in products]
    product_ids = [p.get('ProductID') for p in products]

    # Vectorize
    vectorizer = TfidfVectorizer(stop_words='english', min_df=1) # min_df=1 to allow small datasets
    tfidf_matrix = vectorizer.fit_transform(product_texts)

    # Calculate cosine similarity
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    # Clear old recommendations
    await db.execute(FrequentlyBoughtTogether.__table__.delete())
    await db.commit()

    # Populate recommendation model
    for idx, pid in enumerate(product_ids):
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:6]  # top 5

        for score_idx, score in sim_scores:
            if score > 0.1:
                rec_pid = product_ids[score_idx]
                db.add(FrequentlyBoughtTogether(
                    product_a_id=pid,
                    product_b_id=rec_pid,
                    score=float(score)
                ))
    
    await db.commit()
    logger.info("Successfully updated content-based recommendations.")
