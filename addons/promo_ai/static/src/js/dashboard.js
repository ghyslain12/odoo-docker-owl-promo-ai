/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

class PromoAiDashboard extends Component {
    static template = "promo_ai.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            loading: true,
            sales_total: 0,
            sales_revenue: 0.0,
            sales_discount: 0.0,
            sales_invoiced: 0,
            materials_total: 0,
            materials_with_promo: 0,
            customers_total: 0,
            tickets_open: 0,
            tickets_total: 0,
            promotions_active: 0,
            recent_sales: [],
        });

        // Méthode correcte pour charger les données au démarrage
        onWillStart(async () => {
            await this._loadStats();
        });
    }

    async _loadStats() {
        this.state.loading = true;
        try {
            // --- Sales stats ---
            const allSales = await this.orm.searchRead(
                "promo_ai.sale",
                [],
                ["name", "titre", "customer_id", "total_amount", "total_discount",
                 "ticket_count", "invoice_generated", "create_date"],
                { limit: 100, order: "id desc" }
            );
            this.state.sales_total = allSales.length;
            this.state.sales_revenue = allSales.reduce((sum, s) => sum + (s.total_amount || 0), 0);
            this.state.sales_discount = allSales.reduce((sum, s) => sum + (s.total_discount || 0), 0);
            this.state.sales_invoiced = allSales.filter(s => s.invoice_generated).length;
            this.state.recent_sales = allSales.slice(0, 8);

            // --- Materials ---
            this.state.materials_total = await this.orm.searchCount("promo_ai.material", [["active", "=", true]]);
            this.state.materials_with_promo = await this.orm.searchCount("promo_ai.material", [["active", "=", true], ["active_promotion_id", "!=", false]]);

            // --- Customers ---
            this.state.customers_total = await this.orm.searchCount("promo_ai.customer", []);

            // --- Tickets ---
            this.state.tickets_total = await this.orm.searchCount("promo_ai.ticket", []);
            this.state.tickets_open = await this.orm.searchCount("promo_ai.ticket", [["state", "in", ["new", "in_progress"]]]);

            // --- Promotions ---
            this.state.promotions_active = await this.orm.searchCount("promo_ai.promotion", [["state", "=", "active"]]);
        } catch (e) {
            console.error("Erreur chargement Dashboard:", e);
        } finally {
            this.state.loading = false;
        }
    }

    // Actions pour les boutons
    openSales() { this.action.doAction("promo_ai.action_promo_ai_sale"); }
    openMaterials() { this.action.doAction("promo_ai.action_promo_ai_material"); }
    openCustomers() { this.action.doAction("promo_ai.action_promo_ai_customer"); }
    openTickets() { this.action.doAction("promo_ai.action_promo_ai_ticket"); }
    openPromotions() { this.action.doAction("promo_ai.action_promo_ai_promotion"); }

    async openSale(saleId) {
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "promo_ai.sale",
            res_id: saleId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat("fr-FR", {
            style: "currency",
            currency: "EUR",
            minimumFractionDigits: 2,
        }).format(amount);
    }

    get discountRate() {
        if (!this.state.sales_revenue) return "0%";
        const rate = (this.state.sales_discount / (this.state.sales_revenue + this.state.sales_discount)) * 100;
        return rate.toFixed(1) + "%";
    }
}

// ATTENTION: Le tag doit matcher dashboard_action.xml
registry.category("actions").add("promo_ai.dashboard_tag", PromoAiDashboard);
