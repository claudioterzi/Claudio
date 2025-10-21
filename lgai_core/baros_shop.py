"""
BAROS SHOP - Negozio Ricompense
50 ricompense in 7 categorie
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Reward:
    """Definizione di una ricompensa"""
    id: int
    nome: str
    costo: int
    categoria: str
    descrizione: str
    restrizioni: Optional[str]
    icona: str
    disponibile: bool = True


class BarosShop:
    """Negozio completo ricompense Baros"""

    # CATEGORIA 1: CIBO & BEVANDE
    CIBO_BEVANDE = [
        Reward(1, "🍕 Pizza Take-Away", 150, "Cibo & Bevande",
               "Una pizza intera a scelta, anche con consegna", "Max 2x/mese", "🍕"),
        Reward(2, "🍔 Burger Gourmet", 180, "Cibo & Bevande",
               "Hamburger di qualità con patatine", "Max 2x/mese", "🍔"),
        Reward(3, "🍺 Birra con Amici", 200, "Cibo & Bevande",
               "Serata birre (max 3) con amici", "Max 3x/mese", "🍺"),
        Reward(4, "🍣 Sushi All You Can Eat", 250, "Cibo & Bevande",
               "Cena sushi senza limiti", "Max 1x/mese", "🍣"),
        Reward(5, "🍰 Dolce Artigianale", 100, "Cibo & Bevande",
               "Pasticceria di qualità o gelato artigianale", "Max 4x/mese", "🍰"),
        Reward(6, "☕ Caffetteria Fancy", 80, "Cibo & Bevande",
               "Caffè speciale + dolce in caffetteria bella", "Max 5x/mese", "☕"),
        Reward(7, "🥩 Steakhouse Dinner", 400, "Cibo & Bevande",
               "Cena completa in steakhouse", "Max 1x/mese", "🥩"),
        Reward(8, "🍷 Bottiglia Vino Pregiato", 300, "Cibo & Bevande",
               "Vino di qualità (€30-50)", "Max 1x/mese", "🍷"),
        Reward(9, "🍜 Delivery Preferito", 120, "Cibo & Bevande",
               "Cibo delivery dalla tua app preferita", "Max 3x/mese", "🍜"),
        Reward(10, "🧁 Cheat Meal Totale", 200, "Cibo & Bevande",
               "Qualsiasi pasto 'proibito' senza limite", "Max 2x/mese", "🧁"),
    ]

    # CATEGORIA 2: DIGITALE & INTRATTENIMENTO
    DIGITALE_INTRATTENIMENTO = [
        Reward(11, "📱 1h Extra Social Media", 100, "Digitale & Intrattenimento",
               "Permesso per usare social oltre limite", "Max 4x/mese", "📱"),
        Reward(12, "🎮 Gaming Session 3h", 250, "Digitale & Intrattenimento",
               "Maratona gaming guilt-free", "Max 2x/mese", "🎮"),
        Reward(13, "📺 Binge Serie 4h", 200, "Digitale & Intrattenimento",
               "Netflix/Prime binge senza sensi colpa", "Max 2x/mese", "📺"),
        Reward(14, "🎬 Cinema Solo o con Amici", 180, "Digitale & Intrattenimento",
               "Biglietto cinema + popcorn", "Illimitato", "🎬"),
        Reward(15, "🎵 Concerto/Evento Live", 600, "Digitale & Intrattenimento",
               "Biglietto evento musicale", "Illimitato", "🎵"),
        Reward(16, "🎯 App Premium 1 Mese", 150, "Digitale & Intrattenimento",
               "Sottoscrizione app che vuoi provare", "Illimitato", "🎯"),
        Reward(17, "🎨 Corso Online", 500, "Digitale & Intrattenimento",
               "Udemy/Skillshare/Masterclass", "Illimitato", "🎨"),
        Reward(18, "📱 Device Accessorio", 1000, "Digitale & Intrattenimento",
               "AirPods, smartwatch band, etc", "Max 1x/trimestre", "📱"),
        Reward(19, "🎲 Gioco da Tavolo Nuovo", 400, "Digitale & Intrattenimento",
               "Board game per serata amici", "Illimitato", "🎲"),
        Reward(20, "🎧 Abbonamento Musica 3 Mesi", 300, "Digitale & Intrattenimento",
               "Spotify Premium o simili", "Illimitato", "🎧"),
    ]

    # CATEGORIA 3: RECUPERO & RIPOSO
    RECUPERO_RIPOSO = [
        Reward(21, "🛌 Giorno Riposo Totale", 400, "Recupero & Riposo",
               "Zero abitudini obbligatorie per 1 giorno", "Max 2x/mese", "🛌"),
        Reward(22, "🌅 Sveglia Posticipata", 150, "Recupero & Riposo",
               "Sveglia 2h più tardi senza penalty", "Max 3x/mese", "🌅"),
        Reward(23, "💆 Massaggio Professionale", 600, "Recupero & Riposo",
               "60min massaggio da professionista", "Illimitato", "💆"),
        Reward(24, "🧖 Spa Day", 800, "Recupero & Riposo",
               "Giornata completa spa/terme", "Max 1x/mese", "🧖"),
        Reward(25, "🛏️ Nap Pomeridiano", 100, "Recupero & Riposo",
               "Permesso pisolino 30-60min", "Max 5x/mese", "🛏️"),
        Reward(26, "🏖️ Day Off Spontaneo", 500, "Recupero & Riposo",
               "Giorno libero improvviso (se possibile)", "Max 1x/mese", "🏖️"),
        Reward(27, "🎭 Mental Health Day", 300, "Recupero & Riposo",
               "Giorno dedicato solo a salute mentale", "Max 2x/mese", "🎭"),
        Reward(28, "🧘 Ritiro Meditazione 1 Giorno", 1000, "Recupero & Riposo",
               "Giornata in centro meditazione", "Illimitato", "🧘"),
    ]

    # CATEGORIA 4: SHOPPING & MATERIALE
    SHOPPING_MATERIALE = [
        Reward(29, "🎁 Regalo a Te Stesso <€50", 600, "Shopping & Materiale",
               "Qualsiasi oggetto desiderato entro €50", "Max 2x/mese", "🎁"),
        Reward(30, "👕 Capo Abbigliamento", 800, "Shopping & Materiale",
               "Vestito, scarpe, accessorio", "Max 1x/mese", "👕"),
        Reward(31, "📚 3 Libri Nuovi", 500, "Shopping & Materiale",
               "Libri fisici o ebook", "Illimitato", "📚"),
        Reward(32, "🎨 Materiale Hobby", 700, "Shopping & Materiale",
               "Attrezzatura per hobby (arte, sport, etc)", "Illimitato", "🎨"),
        Reward(33, "💻 Tech Gadget <€100", 1200, "Shopping & Materiale",
               "Accessorio tecnologico", "Max 1x/trimestre", "💻"),
        Reward(34, "🏠 Oggetto Casa", 1000, "Shopping & Materiale",
               "Arredo, decorazione, utilità", "Illimitato", "🏠"),
        Reward(35, "🎒 Zaino/Borsa Qualità", 1500, "Shopping & Materiale",
               "Borsa lavoro o viaggio premium", "Max 1x/semestre", "🎒"),
    ]

    # CATEGORIA 5: ESPERIENZE & VIAGGI
    ESPERIENZE_VIAGGI = [
        Reward(36, "🌴 Weekend Fuori (2 giorni)", 2000, "Esperienze & Viaggi",
               "Viaggio 2 giorni città vicina", "Max 1x/mese", "🌴"),
        Reward(37, "✈️ Volo Low-Cost Europeo", 3000, "Esperienze & Viaggi",
               "Biglietto aereo andata/ritorno", "Illimitato", "✈️"),
        Reward(38, "🏨 Hotel di Lusso 1 Notte", 2500, "Esperienze & Viaggi",
               "5 stelle o boutique hotel", "Max 1x/trimestre", "🏨"),
        Reward(39, "🎢 Parco Divertimenti", 800, "Esperienze & Viaggi",
               "Giornata parco tema con amici", "Illimitato", "🎢"),
        Reward(40, "🏔️ Avventura Outdoor", 1500, "Esperienze & Viaggi",
               "Escursione guidata, parapendio, diving, etc", "Illimitato", "🏔️"),
    ]

    # CATEGORIA 6: RICOMPENSE EPICHE
    RICOMPENSE_EPICHE = [
        Reward(41, "💎 Giorno VIP Totale", 3000, "Ricompense Epiche",
               "24h dove fai TUTTO ciò che vuoi", "Max 1x/mese", "💎"),
        Reward(42, "👑 Settimana Re/Regina", 10000, "Ricompense Epiche",
               "7 giorni con zero restrizioni", "Max 1x/stagione", "👑"),
        Reward(43, "🎯 Achievement Custom", 5000, "Ricompense Epiche",
               "Crea achievement personale + reward", "Illimitato", "🎯"),
        Reward(44, "🔮 Consulenza Personale 2h", 4000, "Ricompense Epiche",
               "Coach/mentore professionista", "Illimitato", "🔮"),
        Reward(45, "🎓 Certificazione Professionale", 8000, "Ricompense Epiche",
               "Corso con certificato ufficiale", "Illimitato", "🎓"),
    ]

    # CATEGORIA 7: INVESTIMENTI IN SÉ
    INVESTIMENTI_IN_SE = [
        Reward(46, "💪 Personal Trainer 5 Sessioni", 3500, "Investimenti in Sé",
               "Allenamento personalizzato", "Illimitato", "💪"),
        Reward(47, "🧠 Terapia/Coaching 3 Sessioni", 4000, "Investimenti in Sé",
               "Supporto psicologico professionale", "Illimitato", "🧠"),
        Reward(48, "🎯 Mentorship 1 Mese", 6000, "Investimenti in Sé",
               "Mentore nel tuo campo per 1 mese", "Illimitato", "🎯"),
        Reward(49, "📊 Software Premium Annuale", 2000, "Investimenti in Sé",
               "Tool professionale (Notion, Adobe, etc)", "Illimitato", "📊"),
        Reward(50, "🌟 Progetto Personale Fund", 5000, "Investimenti in Sé",
               "Budget dedicato a tuo progetto", "Illimitato", "🌟"),
    ]

    @classmethod
    def get_all_rewards(cls) -> List[Reward]:
        """Ritorna tutte le ricompense disponibili"""
        return (
            cls.CIBO_BEVANDE +
            cls.DIGITALE_INTRATTENIMENTO +
            cls.RECUPERO_RIPOSO +
            cls.SHOPPING_MATERIALE +
            cls.ESPERIENZE_VIAGGI +
            cls.RICOMPENSE_EPICHE +
            cls.INVESTIMENTI_IN_SE
        )

    @classmethod
    def get_by_categoria(cls, categoria: str) -> List[Reward]:
        """Ottieni ricompense per categoria"""
        mapping = {
            "Cibo & Bevande": cls.CIBO_BEVANDE,
            "Digitale & Intrattenimento": cls.DIGITALE_INTRATTENIMENTO,
            "Recupero & Riposo": cls.RECUPERO_RIPOSO,
            "Shopping & Materiale": cls.SHOPPING_MATERIALE,
            "Esperienze & Viaggi": cls.ESPERIENZE_VIAGGI,
            "Ricompense Epiche": cls.RICOMPENSE_EPICHE,
            "Investimenti in Sé": cls.INVESTIMENTI_IN_SE,
        }
        return mapping.get(categoria, [])

    @classmethod
    def get_affordable(cls, baros_disponibili: int) -> List[Reward]:
        """Ottieni ricompense che puoi permetterti"""
        all_rewards = cls.get_all_rewards()
        return [r for r in all_rewards if r.costo <= baros_disponibili]

    @classmethod
    def get_by_price_range(cls, min_price: int, max_price: int) -> List[Reward]:
        """Ottieni ricompense in un range di prezzo"""
        all_rewards = cls.get_all_rewards()
        return [r for r in all_rewards if min_price <= r.costo <= max_price]

    @classmethod
    def get_by_id(cls, reward_id: int) -> Optional[Reward]:
        """Ottieni ricompensa per ID"""
        all_rewards = cls.get_all_rewards()
        for reward in all_rewards:
            if reward.id == reward_id:
                return reward
        return None


class PurchaseHistory:
    """Gestisce storico acquisti"""

    def __init__(self):
        self.purchases = []  # Lista di {reward_id, data, costo}

    def add_purchase(self, reward_id: int, costo: int):
        """Registra un acquisto"""
        self.purchases.append({
            'reward_id': reward_id,
            'data': datetime.now().isoformat(),
            'costo': costo
        })

    def get_total_spent(self) -> int:
        """Totale Baros spesi"""
        return sum(p['costo'] for p in self.purchases)

    def get_purchases_by_month(self, month: int, year: int) -> List[dict]:
        """Acquisti di un mese specifico"""
        return [
            p for p in self.purchases
            if datetime.fromisoformat(p['data']).month == month
            and datetime.fromisoformat(p['data']).year == year
        ]

    def can_purchase(self, reward: Reward, current_month: int, current_year: int) -> bool:
        """Verifica se puoi acquistare (controlla restrizioni)"""
        if not reward.restrizioni or reward.restrizioni == "Illimitato":
            return True

        # Conta acquisti di questa ricompensa nel mese
        month_purchases = self.get_purchases_by_month(current_month, current_year)
        count_this_reward = sum(1 for p in month_purchases if p['reward_id'] == reward.id)

        # Estrai limite da restrizioni (es: "Max 2x/mese" -> 2)
        if "Max" in reward.restrizioni and "x/mese" in reward.restrizioni:
            limit = int(reward.restrizioni.split("Max ")[1].split("x/")[0])
            return count_this_reward < limit

        return True


# Test
if __name__ == "__main__":
    print("=== BAROS SHOP LGAI ===\n")

    all_rewards = BarosShop.get_all_rewards()
    print(f"🛒 Totale Ricompense: {len(all_rewards)}\n")

    print("📋 PER CATEGORIA:")
    for cat in ["Cibo & Bevande", "Digitale & Intrattenimento", "Ricompense Epiche"]:
        rewards = BarosShop.get_by_categoria(cat)
        print(f"   {cat}: {len(rewards)} ricompense")

    print("\n💰 ESEMPIO: Con 500 Baros puoi permetterti:")
    affordable = BarosShop.get_affordable(500)
    for r in affordable[:5]:
        print(f"   {r.icona} {r.nome} - {r.costo} Baros")

    print(f"\n   ... e altre {len(affordable) - 5} ricompense!")

    print("\n🏆 TOP 5 RICOMPENSE PIÙ COSTOSE:")
    expensive = sorted(all_rewards, key=lambda x: x.costo, reverse=True)[:5]
    for r in expensive:
        print(f"   {r.icona} {r.nome} - {r.costo} Baros")
