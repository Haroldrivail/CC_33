async function api(endpoint, method = 'GET', data = null) {
    const options = { method, headers: { 'Content-Type': 'application/json' } };
    if (data) options.body = JSON.stringify(data);
    try {
        return await (await fetch(endpoint, options)).json();
    } catch (e) {
        return { success: false, error: e.message };
    }
}

function notify(message, type = 'info') {
    document.querySelector('.notification')?.remove();
    const div = document.createElement('div');
    div.className = `notification alert alert-${type} fade-in`;
    div.style.cssText = 'position:fixed;top:20px;right:20px;z-index:3000;min-width:300px';
    div.innerHTML = `<span>${message}</span><button onclick="this.parentElement.remove()" style="margin-left:auto;background:none;border:none;font-size:1.25rem;cursor:pointer">&times;</button>`;
    document.body.appendChild(div);
    setTimeout(() => div.remove(), 5000);
}

function loader(show, msg = 'Chargement...') {
    let el = document.getElementById('global-loader');
    if (show) {
        if (!el) {
            el = document.createElement('div');
            el.id = 'global-loader';
            el.className = 'loading-overlay';
            el.innerHTML = `<div class="loader"></div><p>${msg}</p>`;
            document.body.appendChild(el);
        }
        el.querySelector('p').textContent = msg;
        el.style.display = 'flex';
    } else if (el) el.style.display = 'none';
}

const session = {
    get: k => JSON.parse(localStorage.getItem(k)),
    set: (k, v) => localStorage.setItem(k, JSON.stringify(v)),
    remove: k => localStorage.removeItem(k),
    getElecteur: () => session.get('electeur'),
    setElecteur: e => session.set('electeur', e),
    getAdmin: () => session.get('admin'),
    setAdmin: a => session.set('admin', a),
    getJeton: (voteId) => session.get(`jeton_${voteId}`),
    setJeton: (voteId, jeton) => session.set(`jeton_${voteId}`, jeton),
    hasVoted: (voteId) => session.get(`voted_${voteId}`) === true,
    markVoted: (voteId) => session.set(`voted_${voteId}`, true),
    isLoggedIn: () => session.getElecteur() !== null,
    isAdmin: () => session.getAdmin() !== null,
    logout: () => { session.remove('electeur'); session.remove('admin'); }
};

const esc = t => { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; };
const formatDate = d => d ? new Date(d).toLocaleDateString('fr-FR', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';

// Authentification
async function loginElecteur(email, password) {
    loader(true, 'Connexion...');
    const r = await api('/api/auth/electeur', 'POST', { email, mot_de_passe: password });
    loader(false);
    if (r.success) { session.setElecteur(r.electeur); notify('Connexion réussie!', 'success'); location.href = 'vote.html'; }
    else notify(r.error || 'Erreur de connexion', 'error');
    return r;
}

async function registerElecteur(nom, prenom, email, password) {
    loader(true, 'Inscription...');
    const r = await api('/api/electeurs/inscription', 'POST', { nom, prenom, email, mot_de_passe: password });
    loader(false);
    notify(r.success ? 'Inscription réussie! Veuillez vous connecter!' : (r.error || 'Erreur lors de l\'inscription'), r.success ? 'success' : 'error');
    return r;
}

async function loginAdmin(username, password) {
    loader(true, 'Connexion...');
    const r = await api('/api/auth/admin', 'POST', { username, mot_de_passe: password });
    loader(false);
    if (r.success) { session.setAdmin(r.admin); notify('Connexion admin réussie!', 'success'); location.href = 'admin.html'; }
    else notify(r.error || 'Erreur', 'error');
    return r;
}

function logout() { loader(true, 'Déconnexion...'); session.logout(); setTimeout(() => { loader(false); notify('Déconnexion réussie', 'success'); location.href = 'index.html'; }, 500); }

// Vote avec jetons anonymes
let selectedOptionId = null;
let currentVoteId = null;
let currentJeton = null;

async function loadOptions(containerId, selectable = false, voteId = null) {
    const c = document.getElementById(containerId);
    if (!c) return;
    c.innerHTML = '<div class="text-center"><div class="loader"></div></div>';

    let r;
    if (voteId) {
        currentVoteId = voteId;
        r = await api(`/api/options/vote?vote_id=${voteId}`);
    } else {
        const v = await api('/api/vote/actif');
        if (!v.success || !v.vote) { c.innerHTML = '<p class="text-center text-muted">Aucun vote actif</p>'; return; }
        currentVoteId = v.vote.id;
        r = await api(`/api/options/vote?vote_id=${v.vote.id}`);
    }

    if (!r.success || !r.options?.length) { c.innerHTML = '<p class="text-center text-muted">Aucune option</p>'; return; }
    c.innerHTML = r.options.map(x => `
        <div class="candidat-card ${selectable ? 'selectable' : ''}" data-id="${x.id}" ${selectable ? `onclick="selectOption(${x.id})"` : ''}>
            <div class="candidat-photo">${x.libelle.substring(0, 2).toUpperCase()}</div>
            <div class="candidat-info">
                <h3>${esc(x.libelle)}</h3>
                <p class="description">${esc(x.description || '')}</p>
            </div>
        </div>`).join('');
}

function selectOption(id) {
    document.querySelectorAll('.candidat-card').forEach(c => c.classList.remove('selected'));
    document.querySelector(`.candidat-card[data-id="${id}"]`)?.classList.add('selected');
    selectedOptionId = id;
    const btn = document.getElementById('vote-btn');
    if (btn) btn.disabled = false;
}

async function demanderJeton() {
    const e = session.getElecteur();
    if (!e || !currentVoteId) return null;

    const jetonCache = session.getJeton(currentVoteId);
    if (jetonCache) {
        currentJeton = jetonCache;
        return jetonCache;
    }

    const r = await api('/api/jeton', 'POST', { electeur_id: e.id, vote_id: currentVoteId });
    if (r.success) {
        session.setJeton(currentVoteId, r.jeton);
        currentJeton = r.jeton;
        return r.jeton;
    }
    return null;
}

async function submitVote() {
    if (!selectedOptionId) { notify('Sélectionnez une option', 'warning'); return; }
    const e = session.getElecteur();
    if (!e) { notify('Connectez-vous', 'error'); location.href = 'index.html'; return; }

    if (session.hasVoted(currentVoteId)) {
        notify('Vous avez déjà voté pour ce vote', 'error');
        return;
    }

    if (!confirm('Confirmer votre vote ?')) return;

    loader(true, 'Enregistrement du vote anonyme...');

    const jeton = await demanderJeton();
    if (!jeton) {
        loader(false);
        notify('Impossible d\'enregistrer votre vote. Vous avez peut-être déjà voté.', 'error');
        return;
    }

    loader(true, 'Enregistrement du vote anonyme...');

    // Étape 2 : Voter avec le jeton (anonyme - pas d'electeur_id)
    const r = await api('/api/voter', 'POST', { jeton: jeton, option_id: selectedOptionId });
    loader(false);

    if (r.success) {
        session.markVoted(currentVoteId);
        notify('Vote anonyme enregistré!', 'success');
        const s = document.getElementById('vote-section');
        if (s) s.innerHTML = `<div class="card text-center"><div style="font-size:4rem;color:var(--secondary-color)">✓</div><h2>Merci!</h2><p>Votre vote a été enregistré de manière anonyme.</p><p class="text-muted">L'administrateur ne peut pas savoir qui a voté.</p><a href="resultats.html" class="btn btn-primary mt-3">Voir les résultats</a></div>`;
    } else notify(r.error || 'Erreur', 'error');
}

// Statistiques et resultats
async function loadStatistiques(id) {
    const c = document.getElementById(id);
    if (!c) return;
    const r = await api('/api/statistiques');
    if (!r.success) return;
    const s = r.statistiques;
    const pl = (n, sing, plur) => n > 1 ? plur : sing;
    c.innerHTML = `
        <div class="stat-card"><div class="stat-value">${s.total_electeurs}</div><div class="stat-label">${pl(s.total_electeurs, 'Électeur', 'votants')}</div></div>
        <div class="stat-card orange"><div class="stat-value">${s.taux_participation}%</div><div class="stat-label">Participation</div></div>
        <div class="stat-card red"><div class="stat-value">${s.total_votes}</div><div class="stat-label">${pl(s.total_votes, 'Vote', 'Votes')}</div></div>`;
}

async function loadResultats(id) {
    const c = document.getElementById(id);
    if (!c) return;
    c.innerHTML = '<div class="text-center"><div class="loader"></div></div>';
    const r = await api('/api/resultats');
    if (!r.success || !r.resultats?.length) { c.innerHTML = '<p class="text-center text-muted">Résultats non disponibles</p>'; return; }
    const total = r.resultats.reduce((s, x) => s + x.nombre_bulletins, 0);
    const max = Math.max(...r.resultats.map(x => x.nombre_bulletins));
    c.innerHTML = r.resultats.map((x, i) => {
        const pct = total > 0 ? ((x.nombre_bulletins / total) * 100).toFixed(1) : 0;
        const win = x.nombre_bulletins === max && i === 0;
        return `<div class="result-item ${win ? 'winner' : ''}">
            <div class="result-header"><h3>${esc(x.libelle)}</h3><span class="result-votes">${x.nombre_bulletins} bulletin(s)</span></div>
            <div class="progress-bar"><div class="progress-bar-fill" style="width:${pct}%"></div></div>
            <div class="result-percentage">${pct}%</div></div>`;
    }).join('');
}


async function addOption(voteId, libelle, description) {
    loader(true, 'Ajout...');
    const r = await api('/api/options', 'POST', { vote_id: voteId, libelle, description });
    loader(false);
    notify(r.success ? 'Option ajoutée!' : (r.error || 'Erreur'), r.success ? 'success' : 'error');
    return r;
}

async function deleteOption(id) {
    if (!confirm('Supprimer cette option ?')) return;
    loader(true, 'Suppression...');
    const r = await api('/api/options/supprimer', 'POST', { id });
    loader(false);
    if (r.success) { notify('Supprimé!', 'success'); loadAdminOptions('options-list'); }
    else notify(r.error || 'Erreur', 'error');
}

async function loadAdminOptions(id) {
    const c = document.getElementById(id);
    if (!c) return;
    const [r, v] = await Promise.all([api('/api/options'), api('/api/votes')]);
    const voteLance = v.votes?.some(x => x.statut === 'active' || x.statut === 'terminee');
    c.innerHTML = r.options?.length ? r.options.map(x => `<tr><td>${x.id}</td><td>${esc(x.libelle)}</td><td>${esc(x.vote_titre || '-')}</td><td>${esc(x.description || '-')}</td><td>${voteLance ? '<span class="text-muted">-</span>' : `<button class="btn btn-danger btn-sm" onclick="deleteOption(${x.id})">Supprimer</button>`}</td></tr>`).join('') : '<tr><td colspan="5" class="text-center">Aucune option</td></tr>';
}

async function loadAdminElecteurs(id) {
    const c = document.getElementById(id);
    if (!c) return;
    const r = await api('/api/electeurs');
    c.innerHTML = r.electeurs?.length ? r.electeurs.map(x => `<tr><td>${x.id}</td><td>${esc(x.prenom)} ${esc(x.nom)}</td><td>${esc(x.email)}</td><td>${formatDate(x.date_inscription)}</td></tr>`).join('') : '<tr><td colspan="4" class="text-center">Aucun électeur</td></tr>';
}

async function createVote(titre, description) {
    loader(true, 'Création...');
    const r = await api('/api/votes', 'POST', { titre, description });
    loader(false);
    notify(r.success ? 'Vote créé!' : (r.error || 'Erreur'), r.success ? 'success' : 'error');
    return r;
}

async function changeVoteStatus(id, statut) {
    loader(true);
    const r = await api('/api/votes/statut', 'POST', { id, statut });
    loader(false);
    if (r.success) { notify('Statut mis à jour!', 'success'); loadAdminVotes('votes-list'); }
    else notify(r.error || 'Erreur', 'error');
}

async function loadAdminVotes(id) {
    const c = document.getElementById(id);
    if (!c) return;
    const r = await api('/api/votes');
    const badge = { en_attente: 'badge-warning', active: 'badge-success', terminee: 'badge-danger' };
    c.innerHTML = r.votes?.length ? r.votes.map(x => `<tr><td>${x.id}</td><td>${esc(x.titre)}</td><td><span class="badge ${badge[x.statut] || ''}">${x.statut}</span></td><td>
        ${x.statut === 'en_attente' ? `<button class="btn btn-secondary btn-sm" onclick="changeVoteStatus(${x.id},'active')">Activer</button>` : ''}
        ${x.statut === 'active' ? `<button class="btn btn-danger btn-sm" onclick="changeVoteStatus(${x.id},'terminee')">Terminer</button>` : ''}
        ${x.statut === 'terminee' ? `<button class="btn btn-primary btn-sm" onclick="decompterBulletins(${x.id})">Décompter</button>` : ''}
    </td></tr>`).join('') : '<tr><td colspan="4" class="text-center">Aucun vote</td></tr>';
}

async function decompterBulletins(voteId) {
    loader(true, 'Décompte des bulletins...');
    const r = await api('/api/decompte', 'POST', { vote_id: voteId });
    loader(false);
    if (r.success) {
        const total = r.resultats?.reduce((s, x) => s + x.nombre_bulletins, 0) || 0;
        const details = r.resultats.map(x => `${x.libelle}: ${x.nombre_bulletins}`).join(' | ');
        const msg = r.deja_calcule
            ? `Résultats déjà calculés - ${details}`
            : `${total} bulletins comptés! ${details}`;
        notify(msg, 'success');
    } else notify(r.error || 'Erreur', 'error');
}

// Navigation
function updateNavigation() {
    const nav = document.getElementById('user-nav');
    if (!nav) return;
    const e = session.getElecteur(), a = session.getAdmin();
    if (e) nav.innerHTML = `<span class="user-name">${esc(e.prenom)} ${esc(e.nom)}</span><button class="btn-logout" onclick="logout()">Déconnexion</button>`;
    else if (a) nav.innerHTML = `<span class="user-name">${esc(a.username)}</span><button class="btn-logout" onclick="logout()">Déconnexion</button>`;
    else nav.innerHTML = `<a href="index.html" class="btn-logout">Connexion</a>`;
}

function requireLogin() { if (!session.getElecteur()) { notify('Connectez-vous', 'warning'); location.href = 'index.html'; return false; } return true; }
function requireAdmin() { if (!session.getAdmin()) { notify('Accès admin requis', 'error'); location.href = 'index.html'; return false; } return true; }

document.addEventListener('DOMContentLoaded', updateNavigation);
