"""Cada porta, contra una entrada bona i contra una de dolenta CONEGUDA.

⛔ Una porta que no pot fallar no és una porta. Aquí, per a cada `PASS` hi ha
d'haver un `FAIL` que demostri que la porta el detecta.
"""
from __future__ import annotations

import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import filtres
import portes as P


class F0(unittest.TestCase):
    def test_esglaons_coherents_passen(self):
        taxes = {0.03125: [100.2, 99.8], 0.0625: [100.1], 0.125: [99.9], 0.25: [100.0]}
        self.assertEqual(P.porta_f0_esglaons(taxes)["estat"], "PASS")

    def test_temps_nominal_en_lloc_del_fisic_falla(self):
        """El cas REAL: 1/30 nominal és 1/32 físic, o sigui un 6,25 % de biaix."""
        taxes = {0.03125: [100.0], 0.0625: [100.0], 0.125: [100.0],
                 0.25: [100.0], 0.03333333: [100.0 * 0.03125 / 0.03333333]}
        r = P.porta_f0_esglaons(taxes)
        self.assertEqual(r["estat"], "FAIL")
        self.assertGreater(abs(r["pitjor_desviacio"]), 0.03)

    def test_fosc_mal_restat_falla(self):
        """Un offset residual fa divergir els esglaons curts, que és el senyal."""
        offset = 3.0
        taxes = {e: [(100.0 * e + offset) / e] for e in (0.001, 0.01, 0.1, 1.0)}
        self.assertEqual(P.porta_f0_esglaons(taxes)["estat"], "FAIL")

    def test_el_terra_de_precisio_eixampla_el_limit(self):
        """Amb esglaons interiorment sorollosos, una discrepancia petita no és res."""
        soroll = {0.03125: [100.0, 106.0], 0.0625: [103.0, 97.0],
                  0.125: [98.0, 104.0], 0.25: [102.0, 96.0]}
        r = P.porta_f0_esglaons(soroll)
        self.assertEqual(r["estat"], "PASS")
        self.assertGreater(r["limit_derivat"], 0.01)

    def test_pero_no_tant_com_per_deixar_passar_un_error_gros(self):
        soroll = {0.03125: [100.0, 106.0], 0.0625: [103.0, 97.0],
                  0.125: [98.0, 104.0], 0.25: [160.0, 154.0]}
        self.assertEqual(P.porta_f0_esglaons(soroll)["estat"], "FAIL")

    def test_amplitud_del_flat_real_passa(self):
        flat = np.linspace(0.9625, 1.0007, 5000)
        r = P.porta_f0_amplitud_flat(flat)
        self.assertEqual(r["estat"], "PASS")
        self.assertLess(r["amplitud_ev"], 0.06)

    def test_flat_massa_agressiu_falla(self):
        self.assertEqual(P.porta_f0_amplitud_flat(np.linspace(0.5, 1.0, 500))["estat"], "FAIL")

    def test_flat_amb_zeros_falla(self):
        self.assertEqual(P.porta_f0_amplitud_flat(np.linspace(0.0, 1.0, 500))["estat"], "FAIL")


class F1(unittest.TestCase):
    def _bo(self, n=42, salt=0.0, t_salt=50.0, soroll=0.4):
        t = np.linspace(0, 100, n)
        rng = np.random.default_rng(7)
        x = 3570.0 + 0.185 * t + rng.normal(0, soroll, n)
        y = 2270.0 - 0.195 * t + rng.normal(0, soroll, n)
        x = x + np.where(t > t_salt, salt, 0.0)
        return t, x, y, [f"f{i}" for i in range(n)]

    def test_deriva_llisa_passa(self):
        r = P.porta_f1_registre(*self._bo())
        self.assertEqual(r["estat"], "PASS")
        self.assertLess(r["separacio_maxima_px"], 0.3)

    def test_salt_de_muntura_falla(self):
        """El cas de la Sony: la muntura patina i el model lineal deixa de valer."""
        r = P.porta_f1_registre(*self._bo(salt=6.0))
        self.assertEqual(r["estat"], "FAIL")

    def test_massa_soroll_al_limbe_falla(self):
        self.assertEqual(P.porta_f1_registre(*self._bo(soroll=4.0))["estat"], "FAIL")

    def test_mesures_nomes_a_mitja_finestra_falla(self):
        t, x, y, n = self._bo()
        x = x.copy(); x[t > 40] = np.nan
        self.assertEqual(P.porta_f1_registre(t, x, y, n)["estat"], "FAIL")

    def test_massa_poques_mesures_falla(self):
        t, x, y, n = self._bo(n=6)
        self.assertEqual(P.porta_f1_registre(t, x, y, n)["estat"], "FAIL")

    def test_cota_de_gir(self):
        self.assertAlmostEqual(P.cota_gir_camp(0.3, 1500.0), math.degrees(0.0002), places=9)


class E(unittest.TestCase):
    def test_perfil_decreixent_passa(self):
        r = np.linspace(1.1, 6.0, 60)
        self.assertEqual(P.porta_e_monotonia(r, 1e-6 * r ** -2.5)["estat"], "PASS")

    def test_anell_de_fusio_falla(self):
        r = np.linspace(1.1, 6.0, 60)
        p = 1e-6 * r ** -2.5
        p[25] *= 1.12                        # un anell del 12 %
        res = P.porta_e_monotonia(r, p)
        self.assertEqual(res["estat"], "FAIL")
        self.assertGreater(res["n_anells_que_pugen"], 0)


class F(unittest.TestCase):
    def _mostra(self, n=6, seed=0):
        rng = np.random.default_rng(seed)
        w = rng.uniform(0.1, 10.0, n)
        v = rng.uniform(1.0, 100.0, n)
        return w, v

    def test_mescla_exacta_passa(self):
        ms = []
        for i in range(20):
            w, v = self._mostra(seed=i)
            ms.append({"id": i, "pesos": w, "valors": v, "compost": (w * v).sum() / w.sum()})
        self.assertEqual(P.porta_f_mescla(ms)["estat"], "PASS")

    def test_composicio_alfa_dependent_de_l_ordre_falla(self):
        """Photoshop no calcula Σ(wI)/Σw: fa alfa i depèn de l'ordre."""
        ms = []
        for i in range(20):
            w, v = self._mostra(seed=i)
            a = w / w.max()
            acc = 0.0
            for ai, vi in zip(a, v):          # «normal» amb opacitat, en ordre
                acc = acc * (1 - ai) + vi * ai
            ms.append({"id": i, "pesos": w, "valors": v, "compost": acc})
        self.assertEqual(P.porta_f_mescla(ms)["estat"], "FAIL")

    def test_mitjana_sense_pesos_falla(self):
        ms = []
        for i in range(20):
            w, v = self._mostra(seed=i)
            ms.append({"id": i, "pesos": w, "valors": v, "compost": v.mean()})
        self.assertEqual(P.porta_f_mescla(ms)["estat"], "FAIL")


class G(unittest.TestCase):
    def test_perfil_net_passa(self):
        r = np.linspace(1.1, 6.0, 80)
        self.assertEqual(P.porta_g_envolupant(r, 1e-6 * r ** -2.5)["estat"], "PASS")

    def test_anomalia_del_doble_falla(self):
        r = np.linspace(1.1, 6.0, 80)
        p = 1e-6 * r ** -2.5
        p[40] *= 2.0
        self.assertEqual(P.porta_g_envolupant(r, p)["estat"], "FAIL")

    def test_sensibilitat_mesurada_de_la_g(self):
        """El límit d'1,30 NO caça un anell del 45 % ni un graó del 40 %.

        Ho deixo escrit com a prova perquè si algú abaixa el límit o canvia el
        PAVA, aquesta prova ha de canviar amb ell i no passar desapercebuda.
        El PAVA absorbeix una pujada agrupant-la amb els veïns.
        """
        r = np.linspace(1.1, 6.0, 80)
        base = 1e-6 * r ** -2.5
        p = base.copy(); p[40:45] *= 1.45
        self.assertEqual(P.porta_g_envolupant(r, p)["estat"], "PASS")
        p = base.copy(); p[40:] *= 1.40
        self.assertEqual(P.porta_g_envolupant(r, p)["estat"], "PASS")

    def test_envolupant_es_decreixent(self):
        v = np.array([5.0, 6.0, 4.0, 4.5, 1.0])
        e = P.envolupant_decreixent(v)
        self.assertTrue(np.all(np.diff(e) <= 1e-12))


class GraonsDeFusio(unittest.TestCase):
    """El perfil de prova imita el de la Vixen: pendent de −11 a 1,09 R☉ i de
    −1,2 a 2,1 R☉. La curvatura és el que fa caure els mètodes d'extrapolació."""

    TRANS = [1.0863, 1.1693, 1.2731, 1.4079, 1.5636, 2.0927]

    def _perfil(self):
        r = np.linspace(1.05, 5.2, 400)
        return r, 1e5 * np.exp(-(np.log(r)) * 7.0) * r ** -1.2 + 470.0

    def test_perfil_corbat_pero_net_no_dona_cap_grao(self):
        r, p = self._perfil()
        res = P.porta_e_graons_de_fusio(r, p, self.TRANS)
        self.assertEqual(res["estat"], "PASS")
        self.assertLess(abs(res["pitjor_grao"]), 0.001)

    def test_grao_del_6_25_per_cent_falla(self):
        """El cas REAL d'aquest pilot: 1/30 nominal contra 1/32 físic."""
        r, p = self._perfil()
        p = p.copy(); p[r > 1.4079] *= 1.0625
        res = P.porta_e_graons_de_fusio(r, p, self.TRANS)
        self.assertEqual(res["estat"], "FAIL")
        self.assertAlmostEqual(res["pitjor_radi_rsol"], 1.404, places=2)

    def test_grao_de_l_1_per_cent_passa(self):
        r, p = self._perfil()
        p = p.copy(); p[r > 1.4079] *= 1.01
        self.assertEqual(P.porta_e_graons_de_fusio(r, p, self.TRANS)["estat"], "PASS")

    def test_soroll_del_mig_per_cent_no_dispara(self):
        r, p = self._perfil()
        rng = np.random.default_rng(3)
        self.assertEqual(P.porta_e_graons_de_fusio(
            r, p * (1 + rng.normal(0, 0.005, p.size)), self.TRANS)["estat"], "PASS")

    def test_la_g_deixaria_passar_el_mateix_grao(self):
        """Les dues portes davant el mateix defecte: la G no el veu, la E2 sí."""
        r, p = self._perfil()
        p = p.copy(); p[r > 1.4079] *= 1.0625
        self.assertEqual(P.porta_g_envolupant(r, p)["estat"], "PASS")
        self.assertEqual(P.porta_e_graons_de_fusio(r, p, self.TRANS)["estat"], "FAIL")

    def test_extrapolar_rectes_donaria_un_fals_positiu(self):
        """Deixat com a prova perquè no es torni a intentar: sobre el perfil NET,
        comparar dues rectes a banda i banda diu −20 % a totes les transicions."""
        r, p = self._perfil()
        lr, lp = np.log10(r), np.log10(p)
        lt = math.log10(1.4079)
        dins = (lr < lt) & (lr >= lt - 0.25)
        fora = (lr > lt) & (lr <= lt + 0.25)
        a1, b1 = np.polyfit(lr[dins], lp[dins], 1)
        a2, b2 = np.polyfit(lr[fora], lp[fora], 1)
        fals = 10.0 ** ((a2 * lt + b2) - (a1 * lt + b1)) - 1.0
        self.assertLess(fals, -0.10)

    def test_sense_transicions_declarades_falla(self):
        r, p = self._perfil()
        self.assertEqual(P.porta_e_graons_de_fusio(r, p, [])["estat"], "FAIL")


class Rectangle(unittest.TestCase):
    def test_imatge_sencera_passa(self):
        self.assertEqual(P.porta_rectangle(np.ones((300, 360)))["estat"], "PASS")

    def test_retall_circular_falla(self):
        """El defecte recurrent: aplicar un filtre dins d'una circumferència."""
        h, w = 300, 360
        yy, xx = np.mgrid[0:h, 0:w]
        d = np.hypot(xx - w / 2, yy - h / 2)
        im = np.where(d < 120, 1.0, np.nan)
        r = P.porta_rectangle(im)
        self.assertEqual(r["estat"], "FAIL")
        self.assertIn("CIRCULAR", r["frontera"])

    def test_petjada_de_sensor_desplacada_passa(self):
        """Un compost centrat al Sol amb el Sol fora del centre del sensor deixa
        una vora sense dada. Això NO és un retall: és cobertura."""
        h, w = 300, 360
        im = np.full((h, w), np.nan)
        im[20:290, 35:350] = 1.0
        self.assertEqual(P.porta_rectangle(im)["estat"], "PASS")

    def test_petjada_girada_passa(self):
        h, w = 400, 400
        yy, xx = np.mgrid[0:h, 0:w]
        a = math.radians(35.0)
        u = (xx - 200) * math.cos(a) + (yy - 200) * math.sin(a)
        v = -(xx - 200) * math.sin(a) + (yy - 200) * math.cos(a)
        im = np.where((np.abs(u) < 150) & (np.abs(v) < 110), 1.0, np.nan)
        self.assertEqual(P.porta_rectangle(im)["estat"], "PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)


class PerfilRadial(unittest.TestCase):
    """⛔ L'entrada dolenta CONEGUDA d'aquesta funció: restar el perfil per calaix.

    Detectat per Pere el 24-08-2026 mirant `fase3_achf_fisiques_flat-si.png`: hi
    havia centenars d'anells concèntrics amb dents de serra. No n'hi havia una
    causa, n'hi havia quatre, i totes viuen a `treu_perfil_radial`. Mesurat amb
    la geometria EXACTA del llenç del pilot i una corona sintètica llisa —o
    sigui que tot el que se'n mesura és artefacte nostre:

    | banda          | abans   | després  |
    |----------------|---------|----------|
    | 1,00-1,15 R☉   | 9,99 %  | 0,232 %  |
    | 1,15-1,50 R☉   | 3,77 %  | 0,0051 % |
    | 1,50-2,50 R☉   | 1,65 %  | 0,0025 % |
    | 2,50-5,00 R☉   | 0,51 %  | 0,0006 % |
    """

    @staticmethod
    def _escena(n_px=1200, r_sol=240.0):
        """Una corona de Baumbach PERFECTAMENT radial, amb el disc lunar fora
        per pes. ⛔ Baumbach i no una potència pura: el que el suavitzat
        esbiaixa és la curvatura, i una potència pura n'amaga la meitat."""
        yy, xx = np.mgrid[0:n_px, 0:n_px]
        r = (np.hypot(xx - n_px / 2, yy - n_px / 2) / r_sol).astype(np.float32)
        x = np.maximum(r, 1.0)
        b = 1e-6 * (0.0532 * x ** -2.5 + 1.425 * x ** -7 + 2.565 * x ** -17)
        return np.log(b).astype(np.float32), (r >= 1.0).astype(np.float32), r

    def test_una_corona_perfectament_radial_no_deixa_residu(self):
        im, pes, r = self._escena()
        d = filtres.treu_perfil_radial(im, pes, r)[0]
        self.assertLess(float(d[pes > 0].std()), 2e-3,
                        "el perfil radial deixa residu estructurat")

    def test_al_limbe_tampoc(self):
        """El limbe és on el perfil és més dret i on l'esglaó era més gros."""
        im, pes, r = self._escena()
        d = filtres.treu_perfil_radial(im, pes, r)[0]
        self.assertLess(float(d[(pes > 0) & (r < 1.15)].std()), 8e-3)

    def test_la_versio_per_calaix_es_deu_vegades_pitjor(self):
        """La versió dolenta, al MATEIX règim de calaix que el llenç de veritat
        (9,475 px; aquí n=70 sobre una escena petita)."""
        im, pes, r = self._escena()
        n = 70
        rv = r[pes > 0]
        vores = np.linspace(float(rv.min()), float(rv.max()), n + 1)
        idx = np.clip(np.digitize(r.ravel(), vores) - 1, 0, n - 1)
        v = im.ravel(); mm = pes.ravel() > 0
        o = np.argsort(idx[mm]); ii = idx[mm][o]; vv = v[mm][o]
        talls = np.searchsorted(ii, np.arange(n + 1))
        med = np.array([np.median(vv[talls[a]:talls[a + 1]])
                        if talls[a + 1] - talls[a] > 50 else np.nan for a in range(n)])
        b = np.isfinite(med)
        med = np.interp(np.arange(n), np.flatnonzero(b), med[b])
        dolent = im - med[idx].reshape(im.shape)
        bo = filtres.treu_perfil_radial(im, pes, r)[0]
        m = pes > 0
        self.assertGreater(float(dolent[m].std()) / float(bo[m].std()), 10.0,
                           "la prova no distingiria la versió dolenta")

    def test_un_calaix_no_pot_ser_sub_pixel(self):
        """Demanar-ne 5.000 sobre un camp petit s'ha de retallar sol."""
        im, pes, r = self._escena(n_px=600, r_sol=120.0)
        _, med, vores = filtres.treu_perfil_radial(im, pes, r, n=5000)
        self.assertLess(len(med), 5000)
        self.assertGreaterEqual(float((vores[1] - vores[0]) * 120.0), 1.0 - 1e-6)

    def test_els_calaixos_son_en_log_r(self):
        """Estrets on el perfil és dret, amples on és pla."""
        im, pes, r = self._escena()
        _, _, vores = filtres.treu_perfil_radial(im, pes, r)
        self.assertGreater((vores[-1] - vores[-2]) / (vores[1] - vores[0]), 2.0)


class E2Uniformitat(unittest.TestCase):
    """⛔ La porta ha de dir el MATEIX número tant si el graó és a 1,2 R☉ com a 5.

    Fins al 24-08-2026 feia servir **un sol** Δlog r —la mediana— sobre calaixos
    uniformes en r, on `diff(log r)` va com 1/r i varia un factor 4,5 al llarg
    del domini. Mesurat amb un graó injectat del +5 %: en deia +1,42 % a 1,20 R☉
    i +8,33 % a 5,00, un factor **5,9** de sensibilitat, i les cinc transicions
    reals del pilot queien totes a la meitat cega.
    """

    @staticmethod
    def _corona(r):
        return 1e-6 * (0.0532 * r ** -2.5 + 1.425 * r ** -7 + 2.565 * r ** -17)

    def _llegit(self, rt, grao=0.05):
        r = np.linspace(1.15, 5.2, 400)      # uniformes en r, com `fase_portes`
        p = self._corona(r).copy()
        p[r >= rt] *= (1.0 + grao)
        res = P.porta_e_graons_de_fusio(r, p, [rt])
        d = res.get("per_transicio") or res.get("detall") or []
        return abs(d[0]["graó"] if d else res.get("pitjor_grao")), res["estat"]

    def test_el_mateix_grao_es_llegeix_igual_a_tot_el_domini(self):
        vals = [self._llegit(rt)[0] for rt in (1.5, 2.0, 3.0, 5.0)]
        self.assertLess(max(vals) / min(vals), 1.25,
                        f"la sensibilitat depèn del radi: {vals}")

    def test_i_el_valor_es_el_de_veritat(self):
        for rt in (1.5, 2.0, 3.0, 5.0):
            v, _ = self._llegit(rt)
            self.assertAlmostEqual(v, 0.05, delta=0.008, msg=f"a {rt} R☉ en diu {v}")

    def test_un_grao_de_l_1_per_cent_es_llegeix_com_a_l_1_per_cent(self):
        for rt in (1.5, 3.0):
            v, _ = self._llegit(rt, 0.01)
            self.assertAlmostEqual(v, 0.01, delta=0.004, msg=f"a {rt} R☉ en diu {v}")


class RectangleInterior(unittest.TestCase):
    """⛔ La porta ha de caçar un tall circular INTERIOR, no només l'exterior.

    Fins al 24-08-2026 només mirava `rmax` per sector: un tall a `rr > 1,12` o
    una rampa de pes circular hi passaven amb `PASS` i
    `variacio_del_radi_maxim = 0,523`. Contra la regla del capdamunt del fitxer.
    """

    @staticmethod
    def _camp(r_dins=None, n=400, r_ocult=40.0):
        yy, xx = np.mgrid[0:n, 0:n]
        r = np.hypot(xx - (n - 1) / 2, yy - (n - 1) / 2)
        im = np.ones((n, n), np.float32)
        im[r < (r_dins if r_dins is not None else r_ocult)] = np.nan
        return im, r_ocult

    def test_nomes_la_lluna_passa(self):
        im, ro = self._camp()
        r = P.porta_rectangle(im, r_ocultador_px=ro)
        self.assertEqual(r["estat"], "PASS")
        self.assertTrue(r["frontera_interior"]["comprovada"])
        self.assertFalse(r["frontera_interior"]["mes_enlla_de_l_ocultador"])

    def test_un_tall_circular_mes_enlla_de_l_ocultador_falla(self):
        im, ro = self._camp(r_dins=100.0)      # 2,5 vegades l'ocultador
        r = P.porta_rectangle(im, r_ocultador_px=ro)
        self.assertEqual(r["estat"], "FAIL")
        self.assertTrue(r["frontera_interior"]["es_circular"])
        self.assertTrue(r["frontera_interior"]["mes_enlla_de_l_ocultador"])

    def test_sense_ocultador_declarat_ho_diu_i_no_aprova_en_silenci(self):
        im, _ = self._camp(r_dins=100.0)
        r = P.porta_rectangle(im)
        self.assertFalse(r["frontera_interior"]["comprovada"])
        self.assertIn("no s'ha declarat", r["frontera_interior"]["motiu"])


# ================================================================ H · artefactes
def _reixa(n=600, r_sol=200.0):
    yy = np.arange(n, dtype=np.float32)[:, None] - n / 2
    xx = np.arange(n, dtype=np.float32)[None, :] - n / 2
    return np.hypot(xx, yy) / r_sol


class H1Circular(unittest.TestCase):
    """Anells concèntrics al detall: el que Pere va marcar en groc el 24-08."""

    def setUp(self):
        self.rr = _reixa()
        self.pes = (self.rr > 1.05).astype(np.float32)
        rng = np.random.default_rng(7)
        self.soroll = (rng.normal(0, 0.0023, self.rr.shape)).astype(np.float32)

    def test_detall_sense_anells_passa(self):
        m = filtres.rms_circular(self.soroll, self.pes, self.rr)
        self.assertEqual(P.porta_h_circular(m["rms_circular"], m["rms_detall"])["estat"], "PASS")

    def test_anells_injectats_fallen(self):
        """Un ondulat circular del 0,15 % sobre un detall del 0,23 %: el cas real."""
        d = self.soroll + (0.0015 * np.sin(2 * np.pi * self.rr / 0.20)).astype(np.float32)
        m = filtres.rms_circular(d, self.pes, self.rr)
        r = P.porta_h_circular(m["rms_circular"], m["rms_detall"])
        self.assertEqual(r["estat"], "FAIL")
        self.assertGreater(r["fraccio"], 0.3)

    def test_la_segona_passada_els_treu(self):
        d = self.soroll + (0.0015 * np.sin(2 * np.pi * self.rr / 0.20)).astype(np.float32)
        net, _, _ = filtres.treu_residu_circular(d, self.pes, self.rr)
        m = filtres.rms_circular(net, self.pes, self.rr)
        self.assertEqual(P.porta_h_circular(m["rms_circular"], m["rms_detall"])["estat"], "PASS")

    def test_la_segona_passada_NO_es_menja_estructura_azimutal(self):
        """⛔ La salvaguarda: restar una constant per anell no pot tocar el que
        varia amb l'angle. Un jet coronal ha de sobreviure sencer."""
        n = self.rr.shape[0]
        yy = np.arange(n, dtype=np.float32)[:, None] - n / 2
        xx = np.arange(n, dtype=np.float32)[None, :] - n / 2
        ang = np.arctan2(yy + 0 * xx, xx + 0 * yy)
        jet = (0.01 * np.cos(6 * ang)).astype(np.float32)
        net, _, _ = filtres.treu_residu_circular(jet, self.pes, self.rr)
        viu = self.pes > 0
        self.assertLess(float(np.std(net[viu] - jet[viu])), 0.05 * float(np.std(jet[viu])))

    def test_el_suavitzat_de_la_primera_passada_deixa_lobuls(self):
        """⛔ La prova que justifica que n'hi hagi d'haver DUES: sobre una corona
        llisa, la primera passada sola deixa un residu circular mesurable."""
        # ⚠️ Al mostreig del llenç de VERITAT: amb R☉ = 120 px un anell de
        # 0,005 R☉ fa 0,6 px i el que es mesura és la pixelització, no cap
        # artefacte. El llenç del pilot té R☉ = 440,6 px.
        rr = _reixa(1400, 440.6)
        pes = (rr > 1.05).astype(np.float32)
        with np.errstate(over="ignore"):
            corona = np.log(np.maximum(rr, 1e-3) ** -2.5
                            + 0.3 * np.maximum(rr, 1e-3) ** -7.0)
        corona = np.where(pes > 0, corona, 0.0).astype(np.float32)
        una, _, _ = filtres.treu_perfil_radial(corona, pes, rr, n=300)
        m1 = filtres.rms_circular(una, pes, rr, r1=1.55)
        self.assertGreater(m1["fraccio"], 0.10)      # la 1a sola deixa un 25 %
        dues, _, _ = filtres.treu_residu_circular(una, pes, rr)
        m2 = filtres.rms_circular(dues, pes, rr, r1=1.55)
        self.assertGreater(m1["rms_circular"], 20 * m2["rms_circular"])
        self.assertEqual(P.porta_h_circular(m2["rms_circular"], m2["rms_detall"])["estat"],
                         "PASS")


class H2Costures(unittest.TestCase):
    """Valls que segueixen una isofota de fusió HDR: el que Pere va marcar en lila."""

    def test_frontera_com_els_controls_passa(self):
        d = [{"nom": "10-11", "es_frontera": True, "contrast": -0.0018, "sigma": 0.0007},
             {"nom": "13-14", "es_frontera": True, "contrast": -0.0016, "sigma": 0.0006},
             {"nom": "ctrl-a", "es_frontera": False, "contrast": -0.0019, "sigma": 0.0006},
             {"nom": "ctrl-b", "es_frontera": False, "contrast": -0.0014, "sigma": 0.0005}]
        self.assertEqual(P.porta_h_costures(d)["estat"], "PASS")

    def test_frontera_que_destaca_dels_controls_falla(self):
        d = [{"nom": "10-11", "es_frontera": True, "contrast": -0.0090, "sigma": 0.0006},
             {"nom": "ctrl-a", "es_frontera": False, "contrast": -0.0008, "sigma": 0.0006},
             {"nom": "ctrl-b", "es_frontera": False, "contrast": +0.0005, "sigma": 0.0005}]
        r = P.porta_h_costures(d)
        self.assertEqual(r["estat"], "FAIL")
        self.assertEqual(r["pitjor_frontera"], "10-11")

    def test_sense_controls_no_hi_ha_porta(self):
        """⛔ El defecte de l'agost: un control de costura que no compara amb res
        deia «0,000 σ» sempre. Sense controls, aquesta porta ha de FALLAR."""
        d = [{"nom": "10-11", "es_frontera": True, "contrast": -0.009, "sigma": 0.0006}]
        self.assertEqual(P.porta_h_costures(d)["estat"], "FAIL")


class H3EsglaonsPixelAPixel(unittest.TestCase):
    def test_esglaons_coherents_passen(self):
        r = {"a": 0.0008, "b": -0.0011, "c": 0.0005}
        self.assertEqual(P.porta_h_esglaons_px(r, {k: 1e-4 for k in r})["estat"], "PASS")

    def test_el_cas_REAL_del_24_08_falla(self):
        """Els números mesurats: signe que alterna i amplitud de l'1,1 al 1,3 %."""
        r = {"1/512→1/256": +0.00519, "1/256→1/128": -0.01105,
             "1/128→1/64": +0.01275, "1/64→1/32": -0.01095,
             "1/32→1/16": +0.01301, "1/16→1/8": -0.01062}
        g = P.porta_h_esglaons_px(r, {k: 1.5e-3 for k in r})
        self.assertEqual(g["estat"], "FAIL")
        self.assertEqual(len(g["parells_que_fallen"]), 6)

    def test_F0_no_te_potencia_per_veure_ho(self):
        """⛔ Per què calia una porta nova: el mateix desacord de l'1,2 %, posat
        a la porta F0 amb la dispersió interna real d'aquell run (2,5-4,3 %),
        hi passa tan tranquil. La porta vella no estava trencada: era cega."""
        taxes = {0.03125: [100.0, 103.5, 97.2], 0.0625: [98.8, 102.6, 96.5],
                 0.125: [101.2, 104.0, 98.1], 0.25: [98.9, 102.0, 96.9]}
        self.assertEqual(P.porta_f0_esglaons(taxes)["estat"], "PASS")


class H3Instrument(unittest.TestCase):
    """⛔ L'instrument que alimenta H3 ha de ser CEC al cel additiu.

    El 24-08-2026 no ho era, i declarava un desacord entre esglaons del 10 %
    allà on la mesura píxel a píxel del mateix compost en donava 1,2: el que
    mesurava era el cel, que varia un 85 % entre fotogrames de la totalitat.
    """

    def _munta(self, cel_per_fotograma, factor_dolent=1.0):
        import pilot
        r = np.exp(np.linspace(np.log(1.15), np.log(7.0), pilot.COH_N))
        corona = 1.0e4 * r ** -2.5
        noms, perfils, exps, cels, fac = [], {}, {}, {}, {}
        for i, (e, cel) in enumerate(cel_per_fotograma):
            n = f"f{i}"
            noms.append(n); exps[n] = e
            c = factor_dolent if e > 0.05 else 1.0
            v = c * (corona + cel)          # P = c·(C + s), com al model
            perfils[n] = {q: (v.copy(), np.full(pilot.COH_N, 5000)) for q in
                          ("R", "G1", "G2", "B")}
            cels[n] = {q: float(cel) for q in ("R", "G1", "G2", "B")}
            fac[n] = {q: float(c) for q in ("R", "G1", "G2", "B")}
        return pilot, perfils, noms, exps, cels, fac

    def test_es_cec_al_cel_que_varia(self):
        """Mateixa corona, cels molt diferents: el desacord ha de ser ~zero."""
        pilot, perfils, noms, exps, cels, fac = self._munta(
            [(0.03125, 300.0), (0.0625, 700.0), (0.125, 310.0), (0.25, 690.0)])
        d = pilot.desacord_entre_esglaons(perfils, noms, exps, cels, fac, False)
        self.assertTrue(d["ratios"], "no ha mesurat cap parell")
        self.assertLess(max(abs(v) for v in d["ratios"].values()), 1e-6)

    def test_veu_un_desacord_multiplicatiu_de_debo(self):
        pilot, perfils, noms, exps, cels, fac = self._munta(
            [(0.03125, 300.0), (0.0625, 700.0), (0.125, 310.0), (0.25, 690.0)],
            factor_dolent=1.012)
        d = pilot.desacord_entre_esglaons(perfils, noms, exps, cels, fac, False)
        g = P.porta_h_esglaons_px(d["ratios"], d["sigmes"])
        self.assertEqual(g["estat"], "FAIL")
        self.assertAlmostEqual(abs(g["pitjor_desacord"]), 0.012, places=4)
        # ⛔ i amb la correcció posada ha de desaparèixer
        d2 = pilot.desacord_entre_esglaons(perfils, noms, exps, cels, fac, True)
        self.assertEqual(P.porta_h_esglaons_px(d2["ratios"], d2["sigmes"])["estat"],
                         "PASS")


class H1Cobertura(unittest.TestCase):
    """⛔ Una escletxa a la vora de la dada no és un anell concèntric."""

    def test_una_escletxa_de_vora_no_compta_com_a_anell(self):
        rr = _reixa(1400, 440.6)
        rng = np.random.default_rng(11)
        det = rng.normal(0, 0.002, rr.shape).astype(np.float32)
        pes = (rr > 1.087).astype(np.float32)
        # una escletxa d'un calaix amb només el 4 % del cercle, i molt brillant
        ang = np.arctan2(*np.indices(rr.shape).astype(np.float32))
        escletxa = (rr > 1.082) & (rr <= 1.087) & (ang < ang.min() + 0.13)
        pes[escletxa] = 1.0
        det[escletxa] += 0.008
        m = filtres.rms_circular(det, pes, rr)
        self.assertEqual(P.porta_h_circular(m["rms_circular"], m["rms_detall"])["estat"],
                         "PASS")

    def test_pero_un_anell_SENCER_de_la_mateixa_amplada_si_que_compta(self):
        rr = _reixa(1400, 440.6)
        rng = np.random.default_rng(11)
        det = rng.normal(0, 0.002, rr.shape).astype(np.float32)
        pes = (rr > 1.082).astype(np.float32)
        det[(rr > 1.082) & (rr <= 1.087)] += 0.008
        # ⛔ un sol anell fi tampoc no ha de disparar la porta si el rms global
        # no se'n ressent; el que ha de disparar-la és una FAMÍLIA d'anells
        d2 = det + (0.0015 * np.sin(2 * np.pi * rr / 0.20)).astype(np.float32)
        m = filtres.rms_circular(d2, pes, rr)
        self.assertEqual(P.porta_h_circular(m["rms_circular"], m["rms_detall"])["estat"],
                         "FAIL")


class CoherenciaSolucionador(unittest.TestCase):
    """L'ajust `P_i(r) = c_i·(C(r) + s_i)` ha de recuperar el que hi has posat."""

    def _dades(self, cs):
        import pilot
        r = np.exp(np.linspace(np.log(1.15), np.log(7.0), pilot.COH_N))
        corona = 1.0e4 * r ** -2.5 + 500.0        # corona + cel MITJÀ
        perfils, noms, t = {}, [], []
        for i, (c, s) in enumerate(cs):
            n = f"f{i}"; noms.append(n); t.append(float(i))
            v = c * (corona + s)
            perfils[n] = {q: (v.copy(), np.full(pilot.COH_N, 5000))
                          for q in ("R", "G1", "G2", "B")}
        return pilot, perfils, noms, np.array(t), corona

    def test_recupera_transparencies_i_cels_NEGATIUS(self):
        """⛔ La prova que hauria evitat l'error del 24-08-2026.

        `s` és la **desviació** respecte del cel mitjà, no el cel absolut: el
        cel de la totalitat fa una V i els fotogrames de mig eclipsi en tenen
        menys que la mitjana. Clavar `s` a zero feia que `c` se'l mengés, i els
        tres fotogrames de 10,079 s queien a 0,947-0,994 quan tocava ~1,00.
        """
        cs = [(1.00, +180.0), (1.03, -160.0), (0.97, +90.0), (1.00, -110.0)]
        pilot, perfils, noms, t, _ = self._dades(cs)
        fac, cels, diag = pilot.ajusta_coherencia(perfils, noms, t, ["G1"])
        g = np.exp(np.median(np.log([c for c, _ in cs])))
        for n, (c, s) in zip(noms, cs):
            self.assertAlmostEqual(fac[n]["G1"], c / g, places=3,
                                   msg=f"{n}: transparència mal recuperada")
        # ⛔ i el cel negatiu ha de sortir negatiu, no clavat a zero
        self.assertLess(cels[noms[1]]["G1"], -50.0)
        self.assertLess(cels[noms[3]]["G1"], -20.0)
        self.assertLess(diag["G1"]["residu_median_percent"], 0.01)

    def test_el_gauge_no_mou_l_escala_absoluta(self):
        """⚠️ `mediana(ln c) = 0`: el fotograma típic queda igual."""
        cs = [(1.00, 0.0), (1.05, 0.0), (0.95, 0.0), (1.02, 0.0), (0.98, 0.0)]
        pilot, perfils, noms, t, _ = self._dades(cs)
        fac, _, _ = pilot.ajusta_coherencia(perfils, noms, t, ["G1"])
        v = np.array([fac[n]["G1"] for n in noms])
        self.assertAlmostEqual(float(np.median(np.log(v))), 0.0, places=6)


class H4JutgeCreuat(unittest.TestCase):
    """⛔ La porta que hauria evitat l'error recurrent del 24-08-2026."""

    REF = {"1.10-1.30": 0.9070, "1.30-1.50": 0.8937, "1.50-1.75": 0.8952,
           "1.75-2.10": 0.9173, "2.10-2.60": 0.8395}

    def test_les_dues_passades_globals_passen(self):
        """Cas REAL: les passades de radi i nivell fan pujar l'acord entre trens."""
        cand = {"1.10-1.30": 0.9301, "1.30-1.50": 0.9520, "1.50-1.75": 0.9456,
                "1.75-2.10": 0.9260, "2.10-2.60": 0.8403}
        r = P.porta_h4_jutge_creuat(self.REF, cand)
        self.assertEqual(r["estat"], "PASS")
        self.assertEqual(r["bandes_que_milloren"], 5)

    def test_la_resta_per_sector_FALLA_encara_que_el_seu_numero_millori(self):
        """⛔ El cas que ho justifica tot: el seu propi estadístic deia que la
        costura d'1,33 R☉ millorava ×8 (−0,072 % → −0,009 %) i el jutge extern
        diu que el que treia era CORONA."""
        ref = {"1.10-1.30": 0.9301, "1.30-1.50": 0.9520, "1.50-1.75": 0.9456,
               "1.75-2.10": 0.9260, "2.10-2.60": 0.8403}
        cand = {"1.10-1.30": 0.8491, "1.30-1.50": 0.9280, "1.50-1.75": 0.9323,
                "1.75-2.10": 0.9125, "2.10-2.60": 0.8389}
        r = P.porta_h4_jutge_creuat(ref, cand)
        self.assertEqual(r["estat"], "FAIL")
        self.assertLess(r["delta_mitja"], 0)

    def test_una_correccio_que_no_toca_res_no_es_una_millora(self):
        r = P.porta_h4_jutge_creuat(self.REF, dict(self.REF))
        self.assertEqual(r["estat"], "FAIL")

    def test_amb_menys_de_tres_bandes_no_hi_ha_jutge(self):
        r = P.porta_h4_jutge_creuat({"a": 0.9, "b": 0.9}, {"a": 0.95, "b": 0.95})
        self.assertEqual(r["estat"], "FAIL")


class RebutsDeParametres(unittest.TestCase):
    """⛔ El 25-08-2026 Codex va enxampar que el rebut podia MENTIR: estampava el
    sostre de la Vixen a tots els rebuts, inclosos els de la Sony, que té el seu.
    Aquestes proves existeixen perquè aquell defecte no pugui tornar."""

    @staticmethod
    def _recarrega(**env):
        """Torna a importar `comu` i `sony` amb l'entorn demanat."""
        import importlib
        vell = {k: os.environ.get(k) for k in env}
        try:
            for k, v in env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            import comu
            import sony
            comu = importlib.reload(comu)
            sony = importlib.reload(sony)
            return comu.parametres_efectius()
        finally:
            for k, v in vell.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            import comu
            import sony
            importlib.reload(comu)
            importlib.reload(sony)

    def test_el_rebut_declara_els_dos_trens_per_separat(self):
        """EL DEFECTE EXACTE: moure el sostre de la Vixen no mou el de la Sony,
        i el rebut ho ha de dir. Abans deia 0,80 als dos."""
        d = self._recarrega(PILOT_SOSTRE="0.80", PILOT_SOSTRE_SONY=None)
        self.assertAlmostEqual(d["vixen"]["sostre_fraccio"], 0.80)
        self.assertAlmostEqual(d["sony"]["sostre_fraccio"], 0.85)
        self.assertNotAlmostEqual(d["vixen"]["sostre_adu"], d["sony"]["sostre_adu"],
                                  delta=100.0)

    def test_cada_tren_te_el_seu_comandament(self):
        d = self._recarrega(PILOT_SOSTRE=None, PILOT_SOSTRE_SONY="0.70")
        self.assertAlmostEqual(d["vixen"]["sostre_fraccio"], 0.85)
        self.assertAlmostEqual(d["sony"]["sostre_fraccio"], 0.70)

    def test_el_tall_dur_i_l_amplada_de_rampa_no_son_el_mateix(self):
        """La confusió del traspàs: `PILOT_SOSTRE` és el tall i `PILOT_RAMPA`
        l'amplada del degradat. El rebut els ha de separar i lligar bé."""
        d = self._recarrega(PILOT_SOSTRE="0.80", PILOT_RAMPA="0.50")
        self.assertAlmostEqual(d["vixen"]["sostre_fraccio"], 0.80)
        self.assertAlmostEqual(d["rampa_amplada"], 0.50)
        self.assertAlmostEqual(d["vixen"]["pes_ple_per_sota_adu"],
                               0.50 * d["vixen"]["sostre_adu"], places=3)

    def test_els_valors_per_defecte_tambe_s_enregistren(self):
        """Un rebut que només diu les variables presents menteix per omissió."""
        d = self._recarrega(PILOT_VOLTES=None)
        c = d["comandaments"]["PILOT_VOLTES"]
        self.assertEqual(c["valor"], "20")
        self.assertTrue(c["per_defecte"])

    def test_cap_variable_del_pilot_no_queda_fora_del_rebut(self):
        """Si algú afegeix una variable nova i no la declara, això falla."""
        import glob
        import re
        arrel = os.path.dirname(os.path.abspath(__file__))
        vistes = set()
        for f in glob.glob(os.path.join(arrel, "*.py")):
            if os.path.basename(f).startswith("test_"):
                continue
            with open(f, encoding="utf-8") as fh:
                vistes |= set(re.findall(r'os\.environ\.get\(\s*"(PILOT_[A-Z_]+)"', fh.read()))
        import comu
        declarades = {c[0] for c in comu.COMANDAMENTS}
        self.assertEqual(vistes - declarades, set(),
                         "variables del pilot sense declarar a COMANDAMENTS")

    def test_desa_json_estampa_i_no_trepitja_el_que_ja_hi_ha(self):
        import json
        import tempfile
        import comu
        with tempfile.TemporaryDirectory() as d:
            p = comu.desa_json(os.path.join(d, "x.json"), {"a": 1})
            amb = json.loads(p.read_text(encoding="utf-8"))
            self.assertIn("parametres_del_pilot", amb)
            self.assertIn("sony", amb["parametres_del_pilot"])
            p2 = comu.desa_json(os.path.join(d, "y.json"),
                                {"a": 1, "parametres_del_pilot": {"meu": True}})
            seu = json.loads(p2.read_text(encoding="utf-8"))
            self.assertEqual(seu["parametres_del_pilot"], {"meu": True})


class AtribucioNivellRadi(unittest.TestCase):
    """⛔ La prova que separa el sensor del camp, contra casos on la resposta és
    CONEGUDA. Sense això no es pot creure el veredicte sobre dades reals: nivell
    i radi estan MOLT correlacionats i qualsevol dels dos pot passar per l'altre.
    """

    @staticmethod
    def _corona(n=180000, llavor=7):
        """Corona sintètica: el nivell cau amb el radi però a radi fix hi ha
        un rang de nivells, que és exactament la palanca que fa servir la prova."""
        rng = np.random.default_rng(llavor)
        radi = 1.05 + 1.35 * rng.random(n)
        az = 360.0 * rng.random(n)
        sector = (az // 10).astype(np.int16)
        # serpentines: el nivell a radi fix varia un factor ~3 amb l'azimut
        estructura = np.exp(0.55 * np.sin(np.radians(2 * az)) + 0.25 * rng.standard_normal(n))
        nivell = 12000.0 * radi ** -3.2 * estructura
        return radi, nivell, sector, rng

    def test_una_dependencia_NOMES_del_nivell_es_diu_SENSOR(self):
        radi, nivell, sector, rng = self._corona()
        u = np.clip(nivell / 13000.0, 0, 1)
        q = 0.012 * u + 0.0015 * rng.standard_normal(radi.size)
        import atribueix_nivell as AN
        d = AN.decompon(q, radi, nivell, sector, n_bootstrap=40)
        v = AN.veredicte(d)
        self.assertEqual(v["veredicte"], "SENSOR")
        self.assertGreater(d["efecte_nivell_a_radi_fix"], 0.002)

    def test_una_dependencia_NOMES_del_radi_es_diu_CAMP(self):
        radi, nivell, sector, rng = self._corona()
        q = 0.012 * (radi - 1.05) / 1.35 + 0.0015 * rng.standard_normal(radi.size)
        import atribueix_nivell as AN
        d = AN.decompon(q, radi, nivell, sector, n_bootstrap=40)
        v = AN.veredicte(d)
        self.assertEqual(v["veredicte"], "CAMP")
        self.assertGreater(d["efecte_radi_a_nivell_fix"], 0.002)

    def test_sense_cap_dependencia_no_s_inventa_res(self):
        radi, nivell, sector, rng = self._corona()
        q = 0.0015 * rng.standard_normal(radi.size)
        import atribueix_nivell as AN
        d = AN.decompon(q, radi, nivell, sector, n_bootstrap=40)
        self.assertEqual(AN.veredicte(d)["veredicte"], "CAP")

    def test_la_correlacio_entre_radi_i_nivell_no_enganya_la_prova(self):
        """⛔ El cas que fa perillosa tota aquesta feina: com que el nivell cau
        amb el radi, una dependència RADIAL pura també produeix un efecte de
        nivell si NO es condiciona. La prova ha de veure el marginal gros i
        matar-lo igualment en condicionar."""
        radi, nivell, sector, rng = self._corona()
        q = 0.012 * (radi - 1.05) / 1.35 + 0.0015 * rng.standard_normal(radi.size)
        # marginal: correlació clara entre q i nivell, sense condicionar
        lo, hi = np.quantile(nivell, [1 / 3, 2 / 3])
        marginal = np.median(q[nivell >= hi]) - np.median(q[nivell <= lo])
        self.assertGreater(abs(marginal), 0.004)      # l'engany existeix
        import atribueix_nivell as AN
        d = AN.decompon(q, radi, nivell, sector, n_bootstrap=40)
        self.assertLess(abs(d["efecte_nivell_a_radi_fix"]), abs(marginal) / 3)


class SufixDelCompostSony(unittest.TestCase):
    """⛔ El defecte del 25-08-2026: `filtres_sony --coh` llegia el compost SENSE
    coherència i escrivia el producte etiquetat `_coh`. Els dos rebuts de fase 3
    de la Sony deien `etiqueta: "sony_llenc_comu"`, o sigui que la cura de les
    costures de fusió no s'havia aplicat mai a aquell tren."""

    def setUp(self):
        import pilot
        self.f = pilot.sufix_sony

    def test_la_coherencia_no_es_pot_perdre_pel_cami(self):
        self.assertEqual(self.f("_coh"), "_coh")
        self.assertEqual(self.f("fisiques_flat-si_coh"), "_coh")

    def test_la_variant_de_cel_es_conserva(self):
        self.assertEqual(self.f("fisiques_flat-si_cel-model"), "_cel-model")
        self.assertEqual(self.f("fisiques_flat-si_cel-color"), "_cel-color")

    def test_cel_i_coherencia_alhora(self):
        self.assertEqual(self.f("fisiques_flat-si_cel-color_coh"), "_cel-color_coh")

    def test_sense_res_es_el_compost_pla(self):
        self.assertEqual(self.f(""), "")
        self.assertEqual(self.f("fisiques_flat-si"), "")

    def test_una_vixen_coherent_no_pot_anar_amb_una_sony_que_no_ho_es(self):
        """La prova que hauria enxampat el defecte: si l'etiqueta de la Vixen
        declara coherència, el sufix de la Sony l'ha de declarar també."""
        for etiqueta in ("fisiques_flat-si_coh", "_coh", "fisiques_flat-no_coh"):
            self.assertIn("_coh", self.f(etiqueta),
                          f"{etiqueta}: la Sony perdria la coherència")


class FiltresDeBrno(unittest.TestCase):
    """Cada filtre contra una entrada de resposta CONEGUDA, i tots contra la
    norma del rectangle: amb dada rectangular no poden inventar-se cap anell."""

    @classmethod
    def setUpClass(cls):
        import filtres_druckmuller as FD
        cls.FD = FD
        h, w = 320, 400
        cls.shape = (h, w)
        cls.centre = (h / 2, w / 2)
        yy = np.arange(h, dtype=np.float32)[:, None] - h / 2
        xx = np.arange(w, dtype=np.float32)[None, :] - w / 2
        cls.r = np.hypot(xx, yy).astype(np.float32)
        cls.phi = np.arctan2(yy * np.ones_like(xx), xx * np.ones_like(yy)).astype(np.float32)
        cls.rsol = 40.0
        # pes: tot el rectangle menys el disc lunar central. ⛔ el rectangle
        # sencer, que és justament el que cap filtre pot retallar.
        cls.w = ((cls.r > cls.rsol)).astype(np.float32)
        # corona llisa: caiguda radial pura, sense cap estructura
        # ⚠️ perfil suau SENSE genoll: amb un `log(x + 0.1)` la curvatura al
        # limbe és tan gran que el passa-alt la treu legítimament i la prova
        # mesuraria la corba, no el filtre.
        # ⚠️ amb OFFSET: si el perfil valgués 0 just al limbe, la convolució
        # ingènua —que hi posa zeros— encertaria per casualitat i la prova de la
        # convolució incompleta no demostraria res.
        cls.llis = (5.0 - 2.5 * np.log(np.maximum(cls.r / cls.rsol, 1.0))).astype(np.float32)
        # ⛔ i una entrada amb estructura AZIMUTAL, per a la prova del rectangle:
        # sobre una entrada purament radial, qualsevol residu és circular per
        # construcció i la prova no podria distingir un filtre bo d'un dolent.
        cls.amb_estructura = (cls.llis
                              + 0.35 * np.cos(3 * cls.phi) * np.exp(-cls.r / 150.0)
                              + 0.20 * np.cos(7 * cls.phi + 1.0)).astype(np.float32)
        # ⛔ i una entrada NOMÉS azimutal, amb soroll: la seva mediana per anell
        # és zero per construcció, o sigui que qualsevol component circular que
        # surti a la sortida se l'ha inventada el filtre. És la prova sincera.
        _rng = np.random.default_rng(20260825)
        cls.nomes_azimutal = (0.35 * np.cos(3 * cls.phi) * np.exp(-cls.r / 150.0)
                              + 0.20 * np.cos(7 * cls.phi + 1.0)
                              + 0.05 * _rng.standard_normal(cls.shape)).astype(np.float32)

    # ---------------------------------------------------------------- passa-alt
    def test_passa_alt_sobre_una_entrada_llisa_dona_gairebe_zero(self):
        d, _ = self.FD.passa_alt(self.llis, self.w, 6.0)
        bo = self.w > 0
        # ⚠️ el 5 % no és laxitud: un passa-alt d'un perfil CORBAT en conserva
        # legítimament la curvatura, i `log r` en té molta prop del limbe.
        self.assertLess(np.std(d[bo]) / np.std(self.llis[bo]), 0.05)

    def test_passa_alt_recupera_una_estructura_coneguda(self):
        bump = (0.20 * np.exp(-((self.r - 90.0) ** 2) / (2 * 4.0 ** 2))
                * np.cos(3 * self.phi)).astype(np.float32)
        d, _ = self.FD.passa_alt(self.llis + bump, self.w, 6.0)
        bo = (self.w > 0) & (np.abs(self.r - 90.0) < 8)
        self.assertGreater(np.corrcoef(d[bo], bump[bo])[0, 1], 0.85)

    def test_el_forat_de_la_lluna_no_deixa_rampa(self):
        """⛔ La convolució incompleta, contra la ingènua, al mateix lloc.

        Amb `gaussian_filter` a seques el zero de dins del forat s'escampa cap
        enfora i el passa-alt el torna a treure com si fos un anell brillant al
        limbe. La prova compara les DUES: la incompleta ha de deixar-hi molt
        menys residu que la ingènua."""
        from scipy.ndimage import gaussian_filter
        bo = self.w > 0
        nostre, _ = self.FD.passa_alt(self.llis, self.w, 8.0)
        ingenu = np.where(bo, self.llis - gaussian_filter(
            np.where(bo, self.llis, 0.0), 8.0, mode="nearest"), 0.0)
        vora = bo & (self.r < self.rsol + 12)
        a = abs(float(np.median(nostre[vora])))
        b = abs(float(np.median(ingenu[vora])))
        self.assertLess(a, b / 5.0, f"incompleta {a:.4g} contra ingènua {b:.4g}")

    # ---------------------------------------------------------- desenfoc radial
    def test_el_desenfoc_azimutal_conserva_un_raig_i_mata_un_anell(self):
        raig = (0.3 * np.exp(-(((self.phi - 0.6 + np.pi) % (2 * np.pi) - np.pi) ** 2)
                             / (2 * 0.05 ** 2))).astype(np.float32)
        anell = (0.3 * np.exp(-((self.r - 90.0) ** 2) / (2 * 1.5 ** 2))).astype(np.float32)
        bo = (self.w > 0) & (self.r > 60) & (self.r < 130)
        br, _ = self.FD.desenfoc_radial(raig, self.w, self.centre, sigma_az_graus=15.0)
        ba, _ = self.FD.desenfoc_radial(anell, self.w, self.centre, sigma_az_graus=15.0)
        # l'anell (estructura radialment estreta) sobreviu al desenfoc azimutal
        self.assertGreater(np.std(ba[bo]) / np.std(anell[bo]), 0.80)
        # el raig (estructura azimutalment estreta) hi queda escampat
        self.assertLess(np.std(br[bo]) / np.std(raig[bo]), 0.50)

    def test_el_desenfoc_radial_fa_exactament_el_contrari(self):
        anell = (0.3 * np.exp(-((self.r - 90.0) ** 2) / (2 * 1.5 ** 2))).astype(np.float32)
        bo = (self.w > 0) & (self.r > 60) & (self.r < 130)
        b, _ = self.FD.desenfoc_radial(anell, self.w, self.centre, sigma_r_px=8.0)
        self.assertLess(np.std(b[bo]) / np.std(anell[bo]), 0.50)

    def test_no_hi_ha_costura_a_l_angle_zero(self):
        """⛔ L'eix de l'angle és circular. Sense `grid-wrap` en tornar de
        polars surt una ratlla radial a φ = 0, que és un artefacte nou."""
        camp = (0.2 * np.cos(2 * self.phi)).astype(np.float32)
        b, _ = self.FD.desenfoc_radial(camp, self.w, self.centre, sigma_az_graus=4.0)
        prop = (self.w > 0) & (self.r > 60) & (self.r < 120) & (np.abs(self.phi) < 0.05)
        lluny = (self.w > 0) & (self.r > 60) & (self.r < 120) & (np.abs(np.abs(self.phi) - 1.5) < 0.05)
        e_prop = float(np.std((b - camp)[prop]))
        e_lluny = float(np.std((b - camp)[lluny]))
        self.assertLess(e_prop, 6 * e_lluny + 1e-4)

    # --------------------------------------------------------------- NRGF/FNRGF
    def test_el_nrgf_esborra_una_caiguda_radial_pura(self):
        import filtres as F
        rs = self.r / self.rsol
        out, _ = self.FD.nrgf(self.llis, self.w, rs)
        # ⚠️ El quocient `std(sortida)/std(entrada)` NO vol dir res: la sortida
        # és en unitats de σ i l'entrada en unitats de la imatge. El que es
        # jutja és si la component RADIAL continua manant a la sortida.
        r1 = self.shape[0] / 2 / self.rsol
        ent = F.rms_circular(self.llis, self.w, rs, r0=1.3, r1=r1, pas_r=0.02)
        sor = F.rms_circular(out, self.w, rs, r0=1.3, r1=r1, pas_r=0.02)
        f_ent = ent["rms_circular"] / max(ent["rms_detall"], 1e-12)
        f_sor = sor["rms_circular"] / max(sor["rms_detall"], 1e-12)
        self.assertGreater(f_ent, 0.75, "l'entrada ha de ser dominantment radial")
        self.assertLess(f_sor, 0.5, f"el NRGF no l'ha aplanada: {f_sor:.2%}")
        self.assertLess(f_sor, f_ent / 2.0)

    def test_el_nrgf_conserva_una_estructura_azimutal(self):
        camp = self.llis + (0.4 * np.cos(3 * self.phi)).astype(np.float32)
        out, _ = self.FD.nrgf(camp, self.w, self.r / self.rsol)
        bo = (self.w > 0) & (self.r > 60) & (self.r < 130)
        self.assertGreater(abs(np.corrcoef(out[bo], np.cos(3 * self.phi)[bo])[0, 1]), 0.8)

    def test_el_fnrgf_si_que_treu_l_asimetria_azimutal(self):
        """La diferència amb el NRGF: aquest sí que pot aplanar una corona molt
        asimètrica, perquè el fons depèn també de l'azimut."""
        camp = self.llis + (0.4 * np.cos(2 * self.phi)).astype(np.float32)
        out, _ = self.FD.fnrgf(camp, self.w, self.r / self.rsol, self.phi, ordre=4)
        bo = (self.w > 0) & (self.r > 60) & (self.r < 130)
        self.assertLess(abs(np.corrcoef(out[bo], np.cos(2 * self.phi)[bo])[0, 1]), 0.35)

    def test_el_fnrgf_declara_els_seus_graus_de_llibertat(self):
        """⚠️ És el filtre amb què més fàcilment es dibuixa el que es vulgui:
        el rebut ha de dir quants paràmetres per anell hi ha."""
        _, d = self.FD.fnrgf(self.llis, self.w, self.r / self.rsol, self.phi, ordre=6)
        self.assertEqual(d["graus_de_llibertat_per_anell"], 2 * (2 * 6 + 1))

    # ------------------------------------------------------------- MGN/WOW/NAFE
    def test_el_mgn_sobre_una_constant_no_inventa_res(self):
        out, _ = self.FD.mgn(np.zeros(self.shape, np.float32) + 3.0, self.w,
                             sigmes=(2, 4, 8))
        self.assertLess(float(np.max(np.abs(out[self.w > 0]))), 1e-3)

    def test_el_wow_ensenya_estructura_feble_de_fora(self):
        feble = (0.02 * np.cos(5 * self.phi) * (self.r > 110)).astype(np.float32)
        fort = (0.50 * np.cos(5 * self.phi) * (self.r < 80)).astype(np.float32)
        out, _ = self.FD.wow(self.llis + feble + fort, self.w, n_escales=4)
        bo_f = (self.w > 0) & (self.r > 115) & (self.r < 140)
        bo_d = (self.w > 0) & (self.r > 50) & (self.r < 75)
        # a l'entrada el de fora és 25× més fluix; a la sortida, molt menys
        self.assertLess(np.std(out[bo_d]) / max(np.std(out[bo_f]), 1e-9), 8.0)

    def test_el_nafe_sobre_una_constant_no_inventa_res(self):
        out, _ = self.FD.nafe(np.zeros(self.shape, np.float32) + 3.0, self.w)
        self.assertLess(float(np.max(np.abs(out[self.w > 0]))), 1e-3)

    # ------------------------------------------- la norma del rectangle, per a tots
    def test_CAP_filtre_no_inventa_un_anell_a_partir_del_rectangle(self):
        """⛔ NORMA DEL RECTANGLE. La dada és rectangular; si un filtre en fes
        sortir una component circular, l'estaria fabricant ell."""
        FD = self.FD
        rs = self.r / self.rsol
        E = self.nomes_azimutal          # mediana per anell = 0 per construcció
        cands = {
            "passa_alt": lambda: FD.passa_alt(E, self.w, 6.0)[0],
            "desenfoc_radial_az": lambda: FD.desenfoc_radial(
                E, self.w, self.centre, sigma_az_graus=5.0)[0],
            "desenfoc_radial_r": lambda: FD.desenfoc_radial(
                E, self.w, self.centre, sigma_r_px=5.0)[0],
            "nrgf": lambda: FD.nrgf(E, self.w, rs)[0],
            "fnrgf": lambda: FD.fnrgf(E, self.w, rs, self.phi, ordre=4)[0],
            "mgn": lambda: FD.mgn(E, self.w, sigmes=(2, 4, 8))[0],
            "wow": lambda: FD.wow(E, self.w, n_escales=4)[0],
            "nafe": lambda: FD.nafe(E, self.w, sigma=20.0)[0],
        }
        import filtres as F
        for nom, fn in cands.items():
            with self.subTest(filtre=nom):
                d = np.where(self.w > 0, fn(), 0.0).astype(np.float32)
                # ⛔ només als radis on el rectangle encara és SENCER: més enllà
                # la manca de dada als cantons és real, no un artefacte.
                dins = (self.w > 0) & (rs > 1.3) & (rs < self.shape[0] / 2 / self.rsol)
                if np.std(d[dins]) < 1e-9:
                    continue
                circ = F.rms_circular(d, dins.astype(np.float32), rs,
                                      r0=1.3, r1=self.shape[0] / 2 / self.rsol,
                                      pas_r=0.02)
                frac = circ["rms_circular"] / max(circ["rms_detall"], 1e-12)
                self.assertLess(frac, 0.20, f"{nom}: component circular {frac:.2%}")

    def test_la_fusio_dels_dos_trens_fa_servir_el_mateix_sufix(self):
        """⛔ El defecte era a DOS llocs: `_dir_sony` i la fusió dels dos trens
        el construïen cadascun pel seu compte i tots dos es menjaven el `_coh`.
        Ara comparteixen funció; això ho fixa."""
        import inspect
        import pilot
        codi = inspect.getsource(pilot.fase_dos_trens_filtrats)
        self.assertIn("sufix_sony(", codi)
        self.assertNotIn('for c in ("_cel-model", "_cel-color")', codi)


class VerificacioDelPSB(unittest.TestCase):
    """⛔ Un PSB de 12 capes que `psd_tools` obria perfectament i que Photoshop
    refusava amb «final de fitxer inesperat». La lliçó: **que la llibreria que
    l'escriu el pugui tornar a llegir no demostra res**."""

    @staticmethod
    def _fals(desti, *, ample=64, alt=64, canals=3, profunditat=16, bytes_per_mostra=None):
        """Fabrica un fitxer amb capçalera de Photoshop i una secció d'Image data
        de la mida que li demanis: així la porta té un cas dolent CONEGUT."""
        import struct
        bps = bytes_per_mostra if bytes_per_mostra is not None else profunditat // 8
        cap = (b"8BPS" + struct.pack(">H", 2) + b"\x00" * 6
               + struct.pack(">HIIHH", canals, alt, ample, profunditat, 3))
        cos = struct.pack(">I", 0) + struct.pack(">I", 0) + struct.pack(">Q", 0)
        dades = struct.pack(">H", 0) + b"\x00" * (ample * alt * canals * bps)
        with open(desti, "wb") as f:
            f.write(cap + cos + dades)

    def setUp(self):
        import munta_photoshop
        self.M = munta_photoshop

    def test_un_fitxer_correcte_passa(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bo.psb"
            self._fals(p)
            r = self.M.verifica_psb(p)
            self.assertEqual(r["estat"], "PASS")
            self.assertEqual(r["bytes_presents"], r["bytes_esperats_si_RAW"])

    def test_LA_MEITAT_DELS_BYTES_falla(self):
        """El cas real: previsualització de 8 bits en un document de 16."""
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "mig.psb"
            self._fals(p, profunditat=16, bytes_per_mostra=1)
            with self.assertRaises(SystemExit) as e:
                self.M.verifica_psb(p)
            self.assertIn("final de fitxer inesperat", str(e.exception))
            self.assertIn("2.0000", str(e.exception))

    def test_tambe_falla_si_en_sobren(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "massa.psb"
            self._fals(p, profunditat=16, bytes_per_mostra=4)
            with self.assertRaises(SystemExit):
                self.M.verifica_psb(p)

    def test_llegeix_la_longitud_de_64_bits_del_PSB(self):
        """⚠️ En PSB la longitud de «layer and mask» és de 8 bytes i en PSD de 4.
        Si la porta la llegís de 4, l'inici d'Image data sortiria desplaçat i el
        veredicte seria fals."""
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bo.psb"
            self._fals(p, ample=32, alt=32)
            r = self.M.verifica_psb(p)
            self.assertEqual(r["amplada_de_les_longituds"], 8)
            self.assertEqual(r["versio"], 2)
            self.assertEqual(r["image_data_inici"], 26 + 4 + 4 + 8)
