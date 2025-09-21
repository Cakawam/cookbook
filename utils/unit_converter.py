# utils/unit_converter.py
class UnitConverter:
    MASS = {'mg': 0.001, 'g': 1.0, 'kg': 1000.0}
    VOLUME = {'ml': 1.0, 'l': 1000.0}
    PIECE = {'un': 1.0}

    @staticmethod
    def to_base(quantity, unit):
        """
        Retorna (quantidade_em_base, unidade_base) onde base é 'g', 'ml' ou 'un'.
        """
        try:
            q = float(quantity)
        except Exception:
            raise ValueError('Quantidade inválida')
        u = (unit or '').lower()
        if u in UnitConverter.MASS:
            return q * UnitConverter.MASS[u], 'g'
        if u in UnitConverter.VOLUME:
            return q * UnitConverter.VOLUME[u], 'ml'
        if u in UnitConverter.PIECE:
            return q, 'un'
        # fallback: return as-is with given unit
        return q, unit

    @staticmethod
    def from_base(quantity, base_unit, target_unit):
        if quantity is None:
            return 0
        try:
            q = float(quantity)
        except Exception:
            return 0
        bu = (base_unit or '').lower()
        tu = (target_unit or '').lower()
        if bu in UnitConverter.MASS and tu in UnitConverter.MASS:
            return q / UnitConverter.MASS[tu]
        if bu in UnitConverter.VOLUME and tu in UnitConverter.VOLUME:
            return q / UnitConverter.VOLUME[tu]
        if bu == 'un' and tu == 'un':
            return q
        return q

    @staticmethod
    def common_units():
        return ['mg','g','kg','ml','l','un']
