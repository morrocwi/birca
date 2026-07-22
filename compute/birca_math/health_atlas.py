#!/usr/bin/env python3
"""
health_atlas.py — 17 standard textbook health-domain models, each self-verified against its own
known qualitative behavior, ALONGSIDE a structural reading of each as a face of the canonical spine.

TWO SEPARATE CLAIMS ARE MADE HERE — DO NOT CONFLATE THEM:

  1. [finite_diagnostic, VERIFIED BY THIS FILE'S __main__] Each of the 17 functions below correctly
     implements a standard textbook model (SIR, one-compartment PK, Gompertz growth, Bergman
     glucose-insulin, etc.) and, when integrated with scipy, reproduces that model's own known
     qualitative behavior (e.g. "SIR: R0>1 outbreak, R0<1 controlled", "PK: t_half=ln2/ke"). This is
     what the self-test actually checks, model by model, in isolation.

  2. [Dr — design-analogy / derived reading, NOT verified by this file] The claim that all 17 of
     these are literally "the same trunk equation read at a different (tau_c, L_R, J, eta)" —

        M d2Phi/dt2 + D dPhi/dt + K L_R Phi + gradV(Phi) = J - eta      (canonical spine)
        telegraph envelope:  tau_c d2u/dt2 + du/dt = D grad^2 u,   tau_c = M/D

     — is a STRUCTURAL / INTERPRETIVE reading asserted in each function's docstring (by analogy:
     "this term plays the role of the restoring operator", "this plays the role of the potential"),
     not a computation that derives each classical model from the spine PDE and shows the
     reduction holds. No test in this file substitutes model-specific (tau_c, L_R, J, eta) into the
     spine equation and confirms it collapses to the classical model, nor does any test compare a
     unification prediction against an independent classical-model prediction. Treat claim (2) at
     the same tier as this repo's own domain-leaf entries in docs/engineering/EQUATION_TREE.md
     (biology/chemistry/etc. as "self-sustained eigenmode" / "reaction-diffusion") -- a design
     analogy that organizes the material, not a machine-checked equivalence.

Sections:
  A. INFECTIOUS DISEASE / EPIDEMIOLOGY   SIR, SEIR, SIRS(endemic), network threshold
  B. WITHIN-HOST / IMMUNOLOGY            viral dynamics (Nowak-May), cytokine-storm bistability
  C. PHARMACOLOGY (PK/PD)                1-compartment, Michaelis-Menten, Hill/Emax
  D. ONCOLOGY                            Gompertz, logistic + treatment threshold
  E. PHYSIOLOGY / HOMEOSTASIS            glucose-insulin (Bergman), FitzHugh-Nagumo, thermostat
  F. CHRONIC / AGING / REPAIR            allostatic burden, cellular aging, wound-healing front

Each function's docstring names its proposed spine-face reading (tau_c, L_R, J, V) as claim (2)
above -- a suggested structural analogy, not a proven reduction.
claim tier: finite_diagnostic (each model's own behavior) / Dr (the spine-unification reading).
readout-not-truth. NOT clinical advice (BIRCA no-diagnosis lock).
References are the originating papers; this file adds no empirical claim of its own.
"""
import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import eigh
import networkx as nx


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'CHECK'}] {name:54} {detail}")
    return bool(cond)


def _peak_time(t, y):
    return t[int(np.argmax(y))]


# =====================================================================================
# A. INFECTIOUS DISEASE / EPIDEMIOLOGY   — spine on a CONTACT GRAPH L_R; threshold = spine lambda_c
# =====================================================================================
def sir(beta, gamma, T=160, i0=1e-3):
    """SIR. spine face: L_R = well-mixed contact graph; R0=beta/gamma is turbulence/smoother ratio,
    threshold R0=1 = spine stability boundary lambda_c. [Kermack-McKendrick 1927]"""
    def rhs(t, z):
        S, I, R = z
        return [-beta*S*I, beta*S*I - gamma*I, gamma*I]
    return solve_ivp(rhs, (0, T), [1-i0, i0, 0], t_eval=np.linspace(0, T, 400), rtol=1e-9)


def seir(beta, sigma, gamma, T=200, i0=1e-3):
    """SEIR. latent compartment E => a memory time tau_lat = 1/sigma; this is the epidemic tau_c
    that delays the peak relative to SIR at the same R0=beta/gamma."""
    def rhs(t, z):
        S, E, I, R = z
        return [-beta*S*I, beta*S*I - sigma*E, sigma*E - gamma*I, gamma*I]
    return solve_ivp(rhs, (0, T), [1-i0, 0, i0, 0], t_eval=np.linspace(0, T, 500), rtol=1e-9)


def sirs(beta, gamma, omega, T=600, i0=1e-3):
    """SIRS with waning immunity omega (R->S). Waning is a restoring current that turns the
    open SIR cascade into a closed loop => an ENDEMIC equilibrium I*>0 (spine fixed point with
    a nonzero source balance), instead of SIR's burn-out I->0."""
    def rhs(t, z):
        S, I, R = z
        return [-beta*S*I + omega*R, beta*S*I - gamma*I, gamma*I - omega*R]
    return solve_ivp(rhs, (0, T), [1-i0, i0, 0], t_eval=np.linspace(0, T, 800), rtol=1e-9)


def network_sis_steady(A, beta, gamma, T=200):
    """Mean-field SIS on an explicit contact graph A (L_R = adjacency). Epidemic threshold is
    beta*lambda_max(A)/gamma = 1, i.e. tau_c^-1 read off the operator spectrum = the spine
    criticality condition. Returns (steady prevalence, lambda_max)."""
    A = np.asarray(A, float)
    lam_max = float(np.max(eigh(A, eigvals_only=True)))
    n = A.shape[0]
    def rhs(t, p):
        return beta*(1-p)*(A @ p) - gamma*p
    p = solve_ivp(rhs, (0, T), np.full(n, 0.05), rtol=1e-9).y[:, -1]
    return float(p.mean()), lam_max


# =====================================================================================
# B. WITHIN-HOST / IMMUNOLOGY
# =====================================================================================
def viral_dynamics(lam=1e4, d=0.1, beta=2e-7, delta=0.5, k=100, c=5, T=200, v0=1.0):
    """Nowak-May target-cell model. T target, I infected, V virus. Basic reproductive ratio
    R0 = beta*lam*k/(d*delta*c). spine face: within-host contact operator; R0>1 => persistent
    infection (nonzero fixed point), R0<1 => clearance (smoother wins). [Nowak & May 2000]"""
    R0 = beta*lam*k/(d*delta*c)
    def rhs(t, z):
        Tc, I, V = z
        return [lam - d*Tc - beta*Tc*V, beta*Tc*V - delta*I, k*I - c*V]
    sol = solve_ivp(rhs, (0, T), [lam/d, 0, v0], t_eval=np.linspace(0, T, 400), rtol=1e-9)
    return sol, R0


def cytokine_storm(a=0.05, b=1.0, Kc=1.0, n=4, dcy=0.55):
    """Pro-inflammatory cytokine with Hill-type positive feedback + linear clearance:
        dC/dt = a + b*C^n/(Kc^n+C^n) - dcy*C.
    The Hill feedback is a double-well potential gradV(C): a LOW 'resolved' attractor and a HIGH
    'storm' attractor separated by an unstable threshold => bistability + hysteresis (the same
    cusp face as BIRCA repair). Returns list of stable fixed points found by multi-start."""
    def settle(C0, T=400):
        f = lambda t, C: [a + b*C[0]**n/(Kc**n + C[0]**n) - dcy*C[0]]
        return solve_ivp(f, (0, T), [C0], rtol=1e-10, atol=1e-12).y[0, -1]
    finals = sorted({round(settle(c0), 3) for c0 in np.linspace(0, 5, 60)})
    # merge numerically-identical attractors
    merged = []
    for v in finals:
        if not merged or abs(v - merged[-1]) > 0.05:
            merged.append(v)
    return merged


# =====================================================================================
# C. PHARMACOLOGY (PK/PD)
# =====================================================================================
def pk_one_compartment(ke=0.3, C0=100.0, T=24):
    """One-compartment IV: dC/dt = -ke*C => first-order decay. spine face: pure damping D
    (M=K=0), tau_c = 0; half-life t_half = ln2/ke. [Fick/Teorell linear PK]"""
    t = np.linspace(0, T, 400)
    return t, C0*np.exp(-ke*t), np.log(2)/ke


def pk_michaelis_menten(Vmax=10.0, Km=5.0, C0=100.0, T=40):
    """Saturable (Michaelis-Menten) elimination: dC/dt = -Vmax*C/(Km+C). At C>>Km: zero-order
    (rate ~ Vmax, capacity-limited); at C<<Km: first-order (rate ~ (Vmax/Km)C). Nonlinear
    damping face of the spine. [Michaelis-Menten 1913; capacity-limited PK]"""
    def rhs(t, C):
        return [-Vmax*C[0]/(Km+C[0])]
    sol = solve_ivp(rhs, (0, T), [C0], t_eval=np.linspace(0, T, 400), rtol=1e-10)
    return sol


def hill_emax(C, Emax=1.0, EC50=1.0, h=1.0):
    """Hill / Emax dose-response: E = Emax*C^h/(EC50^h + C^h). Sigmoid readout map of the spine;
    E(EC50)=Emax/2, steepness set by Hill coefficient h. [Hill 1910]"""
    C = np.asarray(C, float)
    return Emax*C**h/(EC50**h + C**h)


# =====================================================================================
# D. ONCOLOGY
# =====================================================================================
def gompertz(r=0.3, K=1e12, N0=1e9, T=60):
    """Gompertz tumor growth: dN/dt = r*N*ln(K/N). Sigmoid to carrying capacity K; maximum
    growth rate at the inflection N=K/e. spine face: saturating self-limited eigenmode.
    [Gompertz 1825; Laird 1964 tumor fit]"""
    def rhs(t, N):
        return [r*N[0]*np.log(K/N[0])]
    sol = solve_ivp(rhs, (0, T), [N0], t_eval=np.linspace(0, T, 500), rtol=1e-10)
    return sol


def logistic_treatment(r=0.4, K=1e9, c=0.0, N0=1e8, T=120):
    """Logistic tumor with continuous kill term c: dN/dt = r*N*(1-N/K) - c*N. Eradication
    threshold c=r (source vs damping balance): c>r => N->0, c<r => N*=K(1-c/r). spine face:
    logistic potential + damping control c."""
    def rhs(t, N):
        return [r*N[0]*(1-N[0]/K) - c*N[0]]
    sol = solve_ivp(rhs, (0, T), [N0], t_eval=np.linspace(0, T, 500), rtol=1e-10)
    return sol


# =====================================================================================
# E. PHYSIOLOGY / HOMEOSTASIS
# =====================================================================================
def bergman_glucose(p1=0.03, p2=0.025, p3=1.3e-5, Gb=90.0, Ib=10.0,
                    n=0.15, gamma=0.005, h=90.0, G0=250.0, T=180):
    """Bergman minimal model of glucose-insulin regulation (G glucose, X remote insulin action,
    I plasma insulin). Homeostatic setpoint: after a glucose load G0>Gb, negative feedback via
    insulin returns G -> basal Gb. spine face: restoring operator K L_R = the feedback loop.
    [Bergman et al. 1979]"""
    def rhs(t, z):
        G, X, I = z
        dG = -(p1 + X)*G + p1*Gb
        dX = -p2*X + p3*(I - Ib)
        dI = gamma*max(G - h, 0.0)*t*0 + gamma*max(G - h, 0.0) - n*(I - Ib)
        return [dG, dX, dI]
    sol = solve_ivp(rhs, (0, T), [G0, 0, Ib], t_eval=np.linspace(0, T, 600), rtol=1e-9)
    return sol, Gb


def fitzhugh_nagumo(I_ext=0.5, a=0.7, b=0.8, eps=0.08, T=200, v0=-1.2, w0=-0.6):
    """FitzHugh-Nagumo excitable medium (v fast voltage, w slow recovery):
        dv/dt = v - v^3/3 - w + I_ext,   dw/dt = eps*(v + a - b*w).
    Cardiac/neural action potential. For I_ext in the excitable-oscillatory window the rest
    state destabilizes into a LIMIT CYCLE (relaxation oscillation) = self-sustained eigenmode of
    the spine with a cubic nonlinearity gradV. [FitzHugh 1961; Nagumo 1962]"""
    def rhs(t, z):
        v, w = z
        return [v - v**3/3 - w + I_ext, eps*(v + a - b*w)]
    sol = solve_ivp(rhs, (0, T), [v0, w0], t_eval=np.linspace(0, T, 2000), rtol=1e-9)
    return sol


def thermostat(k=0.4, Tset=37.0, T0=41.0, T=40):
    """Thermoregulation as a 1-node restoring spine: dTemp/dt = -k*(Temp - Tset). Fever/chill
    perturbation relaxes back to the homeostatic setpoint Tset. spine face: K L_R with a single
    node, K=k, equilibrium = Tset."""
    def rhs(t, Tv):
        return [-k*(Tv[0] - Tset)]
    sol = solve_ivp(rhs, (0, T), [T0], t_eval=np.linspace(0, T, 300), rtol=1e-10)
    return sol, Tset


# =====================================================================================
# F. CHRONIC / AGING / REPAIR
# =====================================================================================
def allostatic_burden(Sin=1.0, gamma=0.6, B0=0.0, T=60):
    """Allostatic load / BIRCA burden: dB/dt = Sin - gamma*B. Chronic overload (weak clearance
    gamma) accumulates; setpoint B* = Sin/gamma. This is Eq(1) of the monograph read as the
    damped (M=K=0) face of the spine. [McEwen allostatic load; BIRCA Eq(1)]"""
    def rhs(t, B):
        return [Sin - gamma*B[0]]
    sol = solve_ivp(rhs, (0, T), [B0], t_eval=np.linspace(0, T, 300), rtol=1e-10)
    return sol, Sin/gamma


def cellular_aging(p=1.0, Vr=0.7, Km=1.0, A0=0.0, T=80):
    """Cellular aging as irreversible record accumulation under FINITE causal memory (repair
    saturates): dA/dt = p - Vr*A/(Km+A). Max removal capacity = Vr. If production p > Vr the
    record grows without bound (aging is inevitable); if p < Vr it reaches a bounded steady
    state A* = Km*p/(Vr-p). spine face: source J=p vs capacity-limited damping. [Lahtee 2026, ref 1]"""
    def rhs(t, A):
        return [p - Vr*A[0]/(Km + A[0])]
    sol = solve_ivp(rhs, (0, T), [A0], t_eval=np.linspace(0, T, 400), rtol=1e-10)
    bounded = p < Vr
    Astar = Km*p/(Vr - p) if bounded else np.inf
    return sol, bounded, Astar


def wound_healing_front(r=1.0, D=0.25, nx=400, L=100.0, T=30):
    """Wound-healing / tissue-regeneration as a Fisher-KPP traveling front:
        du/dt = D d2u/dx2 + r*u*(1-u).
    The healing edge advances at front speed v = 2*sqrt(r*D). spine face: reaction-diffusion,
    the same K grad^2 + gradV structure as the chemistry leaf. Returns measured front speed."""
    x = np.linspace(0, L, nx); dx = x[1]-x[0]
    u = (x < 5).astype(float)                       # healed tissue on the left
    def lap(u):
        d2 = np.zeros_like(u)
        d2[1:-1] = (u[2:] - 2*u[1:-1] + u[:-2])/dx**2
        d2[0] = d2[1]; d2[-1] = d2[-2]
        return d2
    def rhs(t, u):
        return D*lap(u) + r*u*(1-u)
    ts = np.linspace(0, T, 60)
    sol = solve_ivp(rhs, (0, T), u, t_eval=ts, rtol=1e-7, atol=1e-9, method="RK45")
    def front_x(uu):
        idx = np.where(uu >= 0.5)[0]
        return x[idx[-1]] if len(idx) else 0.0
    xf = np.array([front_x(sol.y[:, j]) for j in range(sol.y.shape[1])])
    # fit speed over the linear (established-front) portion
    m = ts > T*0.4
    v_meas = np.polyfit(ts[m], xf[m], 1)[0]
    return v_meas, 2*np.sqrt(r*D)


# =====================================================================================
if __name__ == "__main__":
    print("=" * 96)
    print("HEALTH-DOMAIN EQUATION ATLAS — each model verified against its own textbook behavior;")
    print("spine-unification reading is a design analogy (Dr), not itself verified here")
    print("=" * 96)
    ok = []

    print("\n-- A. INFECTIOUS DISEASE / EPIDEMIOLOGY  (contact graph L_R ; threshold = spine lambda_c) --")
    s_out = sir(0.5, 0.2); s_ctrl = sir(0.14, 0.2)
    ok.append(check("SIR: R0>1 outbreak, R0<1 controlled",
                    s_out.y[1].max() > 0.1 and s_ctrl.y[1].max() < 0.02,
                    f"peakI R0=2.5:{s_out.y[1].max():.2f}  R0=0.7:{s_ctrl.y[1].max():.3f}"))
    se = seir(0.5, 0.2, 0.2); si = sir(0.5, 0.2)
    ok.append(check("SEIR: latent tau_c delays the peak vs SIR (same R0)",
                    _peak_time(se.t, se.y[2]) > _peak_time(si.t, si.y[1]),
                    f"t_peak SEIR={_peak_time(se.t,se.y[2]):.0f} > SIR={_peak_time(si.t,si.y[1]):.0f}"))
    ss = sirs(0.5, 0.2, 0.05)
    ok.append(check("SIRS: waning immunity -> endemic equilibrium I*>0",
                    ss.y[1, -1] > 0.01, f"I(inf)={ss.y[1,-1]:.3f} (SIR would be ~0)"))
    G = nx.barabasi_albert_graph(60, 3, seed=1); A = nx.to_numpy_array(G)
    gamma = 1.0; lam_max = float(np.max(eigh(A, eigvals_only=True)))
    p_above, _ = network_sis_steady(A, beta=1.5/lam_max, gamma=gamma)
    p_below, _ = network_sis_steady(A, beta=0.6/lam_max, gamma=gamma)
    ok.append(check("network SIS: spreads iff beta*lambda_max/gamma>1 (= spine lambda_c)",
                    p_above > 0.05 and p_below < 1e-3,
                    f"lam_max={lam_max:.2f}  prev above={p_above:.3f} below={p_below:.1e}"))

    print("\n-- B. WITHIN-HOST / IMMUNOLOGY --")
    sv_hi, R0_hi = viral_dynamics(beta=2e-6)     # R0 = beta*4e6 = 8 > 1  -> persists
    sv_lo, R0_lo = viral_dynamics(beta=1e-7)     # R0 = 0.4 < 1           -> clears
    ok.append(check("viral dynamics: R0>1 persists, R0<1 clears",
                    sv_hi.y[2, -1] > 1 and sv_lo.y[2, -1] < 1,
                    f"R0={R0_hi:.1f} V*={sv_hi.y[2,-1]:.0f} | R0={R0_lo:.2f} V*={sv_lo.y[2,-1]:.1e}"))
    wells = cytokine_storm()
    ok.append(check("cytokine storm: Hill feedback -> BISTABLE (resolved vs storm)",
                    len(wells) == 2, f"stable C* = {wells}"))

    print("\n-- C. PHARMACOLOGY (PK/PD) --")
    t, C, thalf = pk_one_compartment()
    ok.append(check("PK 1-compartment: C(t_half)=C0/2, t_half=ln2/ke",
                    abs(np.interp(thalf, t, C) - 50.0) < 0.5, f"t_half={thalf:.2f} C={np.interp(thalf,t,C):.1f}"))
    mm = pk_michaelis_menten()
    early = -(mm.y[0, 5] - mm.y[0, 0])/(mm.t[5]-mm.t[0])
    late = -(mm.y[0, -1] - mm.y[0, -6])/(mm.t[-1]-mm.t[-6])
    ok.append(check("PK Michaelis-Menten: zero-order (fast) high C -> first-order (slow) low C",
                    early > 1.5*late, f"|dC/dt| early={early:.2f} > late={late:.2f}"))
    E_half = hill_emax(1.0, EC50=1.0)
    steep = hill_emax(2.0, h=4) - hill_emax(1.0, h=4)
    shallow = hill_emax(2.0, h=1) - hill_emax(1.0, h=1)
    ok.append(check("Hill/Emax: E(EC50)=Emax/2 and larger h is steeper",
                    abs(E_half-0.5) < 1e-9 and steep > shallow, f"E(EC50)={E_half:.2f}"))

    print("\n-- D. ONCOLOGY --")
    gz = gompertz()
    idx_inf = np.argmax(np.gradient(gz.y[0], gz.t))
    ok.append(check("Gompertz: saturates to K, max growth at N~K/e",
                    gz.y[0, -1] > 0.95e12 and 0.2e12 < gz.y[0, idx_inf] < 0.55e12,
                    f"N(inf)={gz.y[0,-1]:.2e} N_inflect={gz.y[0,idx_inf]:.2e} (K/e={1e12/np.e:.2e})"))
    cured = logistic_treatment(c=0.6); grew = logistic_treatment(c=0.1)
    ok.append(check("logistic tumor: kill c>r eradicates, c<r persists (threshold c=r)",
                    cured.y[0, -1] < 1e6 and grew.y[0, -1] > 1e8,
                    f"c>r: N={cured.y[0,-1]:.1e}  c<r: N={grew.y[0,-1]:.1e}"))

    print("\n-- E. PHYSIOLOGY / HOMEOSTASIS --")
    bg, Gb = bergman_glucose()
    ok.append(check("Bergman glucose: returns to basal Gb after a load (homeostasis)",
                    abs(bg.y[0, -1] - Gb) < 8, f"G(inf)={bg.y[0,-1]:.1f} -> Gb={Gb:.0f}"))
    fhn = fitzhugh_nagumo(I_ext=0.5)
    amp = fhn.y[0, 500:].max() - fhn.y[0, 500:].min()
    ok.append(check("FitzHugh-Nagumo: sustained limit-cycle oscillation (action potentials)",
                    amp > 1.5, f"osc amplitude={amp:.2f}"))
    th, Tset = thermostat()
    ok.append(check("thermostat: fever relaxes to setpoint Tset",
                    abs(th.y[0, -1] - Tset) < 0.1, f"T(inf)={th.y[0,-1]:.2f} -> {Tset}"))

    print("\n-- F. CHRONIC / AGING / REPAIR --")
    ab, Bstar = allostatic_burden()
    ok.append(check("allostatic burden: settles at B*=Sin/gamma",
                    abs(ab.y[0, -1] - Bstar) < 0.02, f"B(inf)={ab.y[0,-1]:.2f} -> {Bstar:.2f}"))
    ag_un, bnd_un, _ = cellular_aging(p=1.0, Vr=0.7)      # p>Vr -> unbounded
    ag_bd, bnd_bd, As = cellular_aging(p=0.4, Vr=0.7)     # p<Vr -> bounded
    ok.append(check("cellular aging: p>capacity Vr -> unbounded record; p<Vr -> bounded",
                    (not bnd_un) and bnd_bd and ag_un.y[0, -1] > 3*ag_bd.y[0, -1],
                    f"A(p>Vr)={ag_un.y[0,-1]:.1f} unbounded | A*(p<Vr)={As:.2f}"))
    v_meas, v_theory = wound_healing_front()
    ok.append(check("wound healing: Fisher-KPP front speed v=2*sqrt(rD)",
                    abs(v_meas - v_theory)/v_theory < 0.20,
                    f"v_meas={v_meas:.2f} vs 2*sqrt(rD)={v_theory:.2f}"))

    print("\n" + "=" * 96)
    print(f"HEALTH ATLAS: {sum(ok)}/{len(ok)} models verified against their OWN known textbook")
    print("behavior by real integration [finite_diagnostic]. This does NOT verify that they are all")
    print("literally one trunk equation M Phi_tt + D Phi_t + K L_R Phi + gradV(Phi) = J - eta at")
    print("different (tau_c, L_R, J, eta) -- that spine-unification reading is a structural/design")
    print("analogy asserted in each docstring [Dr], not a derivation this test checks. No test here")
    print("substitutes a model's parameters into the spine PDE and confirms the reduction holds.")
    print("claim tier: finite_diagnostic (each model's own behavior) / Dr (spine-unification reading).")
    print("readout-not-truth. NOT clinical advice (BIRCA lock).")
    print("=" * 96)
    import sys
    sys.exit(0 if sum(ok) == len(ok) else 1)
