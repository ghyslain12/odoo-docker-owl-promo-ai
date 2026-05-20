# -*- coding: utf-8 -*-
"""
Migration 19.0.1.1.0
- Reserved for future schema changes
- Example: add coupon_code index on promo_ai.sale
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    _logger.info("promo_ai: running migration from %s to 19.0.1.1.0", version)
    cr.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'promo_ai_sale'
                AND indexname = 'promo_ai_sale_coupon_code_idx'
            ) THEN
                CREATE INDEX promo_ai_sale_coupon_code_idx
                ON promo_ai_sale(coupon_code)
                WHERE coupon_code IS NOT NULL;
            END IF;
        END $$;
    """)
    _logger.info("promo_ai: migration 19.0.1.1.0 done")
