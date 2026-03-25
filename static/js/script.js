const state = {
    config: null,
    projects: [],
    currentProject: null,
};

const elements = {
    projectList: document.getElementById('projectList'),
    projectCountBadge: document.getElementById('projectCountBadge'),
    currentProjectState: document.getElementById('currentProjectState'),
    formMessage: document.getElementById('formMessage'),
    heroPlanScore: document.getElementById('heroPlanScore'),
    heroFactScore: document.getElementById('heroFactScore'),
    planFactors: document.getElementById('planFactors'),
    planResults: document.getElementById('planResults'),
    planMeasures: document.getElementById('planMeasures'),
    planTotalBadge: document.getElementById('planTotalBadge'),
    factMeasures: document.getElementById('factMeasures'),
    factResults: document.getElementById('factResults'),
    factMeasuresResult: document.getElementById('factMeasuresResult'),
    factTotalBadge: document.getElementById('factTotalBadge'),
    statsSummary: document.getElementById('statsSummary'),
    statsStages: document.getElementById('statsStages'),
    statsProjects: document.getElementById('statsProjects'),
};

document.addEventListener('DOMContentLoaded', async () => {
    bindEvents();
    await loadInitialState();
});

function bindEvents() {
    document.getElementById('newProjectBtn').addEventListener('click', resetProjectForm);
    document.getElementById('saveProjectBtn').addEventListener('click', saveProject);
    document.getElementById('calculatePlanBtn').addEventListener('click', calculatePlan);
    document.getElementById('calculateFactBtn').addEventListener('click', calculateFact);
    document.getElementById('loadStatsBtn').addEventListener('click', loadStatistics);

    document.querySelectorAll('.tab-button').forEach((button) => {
        button.addEventListener('click', () => activateTab(button.dataset.tab));
    });
}

async function loadInitialState() {
    try {
        const [configResponse, projectsResponse] = await Promise.all([
            fetch('/api/config'),
            fetch('/api/projects'),
        ]);
        state.config = await configResponse.json();
        state.projects = (await projectsResponse.json()).projects || [];

        renderPlanFactors();
        renderFactInputs();
        renderProjectList();
        await loadStatistics();
    } catch (error) {
        showMessage(`Не удалось загрузить приложение: ${error.message}`, true);
    }
}

function activateTab(tabId) {
    document.querySelectorAll('.tab-button').forEach((button) => {
        button.classList.toggle('is-active', button.dataset.tab === tabId);
    });
    document.querySelectorAll('.tab-panel').forEach((panel) => {
        panel.classList.toggle('is-active', panel.id === tabId);
    });
}

function resetProjectForm() {
    state.currentProject = null;
    document.getElementById('projectForm').reset();
    document.getElementById('projectId').value = '';
    elements.currentProjectState.textContent = 'Новый проект';
    elements.planResults.classList.add('hidden');
    elements.factResults.classList.add('hidden');
    updateHeroScores();
    renderPlanFactors();
    renderFactInputs();
    showMessage('Форма проекта очищена.');
}

function projectFormPayload() {
    return {
        id: document.getElementById('projectId').value || undefined,
        name: document.getElementById('projectName').value.trim(),
        code: document.getElementById('projectCode').value.trim(),
        project_group: document.getElementById('projectGroup').value.trim(),
        stage: document.getElementById('projectStage').value.trim(),
        start_date: document.getElementById('projectStartDate').value,
        end_date: document.getElementById('projectEndDate').value,
        project_manager: document.getElementById('projectManager').value.trim(),
        chief_engineer: document.getElementById('chiefEngineer').value.trim(),
        design_lead: document.getElementById('designLead').value.trim(),
    };
}

async function saveProject() {
    try {
        const response = await fetch('/api/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(projectFormPayload()),
        });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error((payload.details || []).join(' ') || payload.error || 'Ошибка сохранения.');
        }

        state.currentProject = payload;
        document.getElementById('projectId').value = payload.id;
        elements.currentProjectState.textContent = `${payload.name} (${payload.code})`;
        showMessage('Проект сохранен.');
        await refreshProjects(payload.id);
    } catch (error) {
        showMessage(error.message, true);
    }
}

async function refreshProjects(selectedId = null) {
    const response = await fetch('/api/projects');
    state.projects = (await response.json()).projects || [];
    renderProjectList(selectedId || state.currentProject?.id);
    await loadStatistics();
}

function renderProjectList(selectedId = null) {
    elements.projectCountBadge.textContent = state.projects.length;
    elements.projectList.innerHTML = '';

    if (!state.projects.length) {
        elements.projectList.innerHTML = '<p class="empty-state">Пока нет сохраненных проектов.</p>';
        return;
    }

    state.projects.forEach((project) => {
        const button = document.createElement('button');
        button.className = 'project-item';
        if ((selectedId && project.id === selectedId) || (state.currentProject && project.id === state.currentProject.id)) {
            button.classList.add('is-active');
        }
        button.innerHTML = `
            <strong>${escapeHtml(project.name || 'Без названия')}</strong>
            <span>${escapeHtml(project.code || '')}</span>
            <small>PLAN: ${formatScore(project.plan_score)} | FACT: ${formatScore(project.fact_score)}</small>
        `;
        button.addEventListener('click', () => loadProject(project.id));
        elements.projectList.appendChild(button);
    });
}

async function loadProject(projectId) {
    try {
        const response = await fetch(`/api/projects/${projectId}`);
        const project = await response.json();
        if (!response.ok) {
            throw new Error(project.error || 'Не удалось загрузить проект.');
        }

        state.currentProject = project;
        fillProjectForm(project);
        renderPlanFactors(project.plan_inputs || {});
        renderFactInputs(project.fact_inputs || {});
        renderPlanResults(project.plan_result);
        renderFactResults(project.fact_result);
        updateHeroScores();
        renderProjectList(project.id);
        showMessage(`Открыт проект: ${project.name}`);
    } catch (error) {
        showMessage(error.message, true);
    }
}

function fillProjectForm(project) {
    document.getElementById('projectId').value = project.id || '';
    document.getElementById('projectName').value = project.name || '';
    document.getElementById('projectCode').value = project.code || '';
    document.getElementById('projectGroup').value = project.project_group || '';
    document.getElementById('projectStage').value = project.stage || '';
    document.getElementById('projectStartDate').value = project.start_date || '';
    document.getElementById('projectEndDate').value = project.end_date || '';
    document.getElementById('projectManager').value = project.project_manager || '';
    document.getElementById('chiefEngineer').value = project.chief_engineer || '';
    document.getElementById('designLead').value = project.design_lead || '';
    elements.currentProjectState.textContent = `${project.name} (${project.code})`;
}

function renderPlanFactors(selectedInputs = {}) {
    if (!state.config) return;

    elements.planFactors.innerHTML = '';
    state.config.plan_factors.forEach((factor) => {
        const card = document.createElement('div');
        card.className = 'factor-card';
        const options = factor.options.map((option) => {
            const selected = selectedInputs[factor.key] === option.code ? 'selected' : '';
            return `<option value="${option.code}" ${selected}>${escapeHtml(option.label)} (${option.value})</option>`;
        }).join('');

        card.innerHTML = `
            <label>
                <span>${escapeHtml(factor.name)}</span>
                <select data-plan-factor="${factor.key}">
                    <option value="">Выберите оценку</option>
                    ${options}
                </select>
            </label>
            <p class="factor-hint">${escapeHtml(factor.key)}</p>
        `;
        elements.planFactors.appendChild(card);
    });
}

function renderFactInputs(selectedInputs = {}) {
    if (!state.config) return;

    const rows = state.config.fact_measures.map((measure) => `
        <div class="fact-row">
            <div>
                <strong>${escapeHtml(measure.name)}</strong>
                <p class="muted">Вес: ${measure.weight} | Границы: ${measure.worst} -> ${measure.best}</p>
                <p class="reference-text">${measure.reference_levels.map(escapeHtml).join(' | ')}</p>
            </div>
            <label>
                <span>Факт</span>
                <input type="number" step="0.0001" data-fact-measure="${measure.key}" value="${selectedInputs[measure.key] ?? ''}">
            </label>
        </div>
    `).join('');

    elements.factMeasures.innerHTML = rows;
}

async function ensureProjectSaved() {
    if (document.getElementById('projectId').value) {
        return document.getElementById('projectId').value;
    }

    await saveProject();
    return document.getElementById('projectId').value;
}

async function calculatePlan() {
    try {
        const projectId = await ensureProjectSaved();
        if (!projectId) {
            throw new Error('Сначала сохраните проект.');
        }

        const inputs = {};
        document.querySelectorAll('[data-plan-factor]').forEach((select) => {
            inputs[select.dataset.planFactor] = select.value;
        });

        const response = await fetch(`/api/projects/${projectId}/plan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ inputs }),
        });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error((payload.details || []).join(' ') || payload.error || 'Ошибка расчета PLAN.');
        }

        state.currentProject = payload;
        renderPlanResults(payload.plan_result);
        updateHeroScores();
        await refreshProjects(projectId);
        showMessage('PLAN пересчитан и сохранен.');
    } catch (error) {
        showMessage(error.message, true);
    }
}

async function calculateFact() {
    try {
        const projectId = await ensureProjectSaved();
        if (!projectId) {
            throw new Error('Сначала сохраните проект.');
        }

        const inputs = {};
        document.querySelectorAll('[data-fact-measure]').forEach((input) => {
            inputs[input.dataset.factMeasure] = input.value;
        });

        const response = await fetch(`/api/projects/${projectId}/fact`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ inputs }),
        });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error((payload.details || []).join(' ') || payload.error || 'Ошибка расчета FACT.');
        }

        state.currentProject = payload;
        renderFactResults(payload.fact_result);
        updateHeroScores();
        await refreshProjects(projectId);
        showMessage('FACT пересчитан и сохранен.');
    } catch (error) {
        showMessage(error.message, true);
    }
}

function renderPlanResults(result) {
    if (!result) {
        elements.planResults.classList.add('hidden');
        return;
    }

    elements.planResults.classList.remove('hidden');
    elements.planTotalBadge.textContent = formatScore(result.total_score);

    const rows = result.measures.map((measure) => `
        <div class="measure-row">
            <div>
                <strong>${escapeHtml(measure.name)}</strong>
                <p class="muted">Intercept: ${measure.intercept} | Raw: ${measure.raw_value} | Weight: ${measure.weight}</p>
            </div>
            <div class="measure-values">
                <span>Score: ${measure.normalized_score}</span>
                <span>Weighted: ${measure.weighted_score}</span>
            </div>
        </div>
    `).join('');

    elements.planMeasures.innerHTML = rows;
}

function renderFactResults(result) {
    if (!result) {
        elements.factResults.classList.add('hidden');
        return;
    }

    elements.factResults.classList.remove('hidden');
    elements.factTotalBadge.textContent = formatScore(result.total_score);

    const rows = result.measures.map((measure) => `
        <div class="measure-row">
            <div>
                <strong>${escapeHtml(measure.name)}</strong>
                <p class="muted">Факт: ${measure.actual_value} | Weight: ${measure.weight}</p>
            </div>
            <div class="measure-values">
                <span>Score: ${measure.normalized_score}</span>
                <span>Weighted: ${measure.weighted_score}</span>
            </div>
        </div>
    `).join('');

    elements.factMeasuresResult.innerHTML = rows;
}

async function loadStatistics() {
    const params = new URLSearchParams({
        project_group: document.getElementById('statsGroup').value,
        specialist: document.getElementById('statsSpecialist').value,
        date_from: document.getElementById('statsDateFrom').value,
        date_to: document.getElementById('statsDateTo').value,
    });

    const response = await fetch(`/api/statistics?${params.toString()}`);
    const payload = await response.json();

    const summary = payload.summary;
    elements.statsSummary.innerHTML = `
        <div class="stat-card"><span>Проектов</span><strong>${summary.project_count}</strong></div>
        <div class="stat-card"><span>Средний PLAN</span><strong>${formatScore(summary.average_plan_score)}</strong></div>
        <div class="stat-card"><span>Средний FACT</span><strong>${formatScore(summary.average_fact_score)}</strong></div>
        <div class="stat-card"><span>Разрыв FACT - PLAN</span><strong>${formatScore(summary.average_gap_fact_minus_plan)}</strong></div>
    `;

    elements.statsStages.innerHTML = payload.stage_distribution.length
        ? payload.stage_distribution.map((item) => `<span class="stage-pill">${escapeHtml(item.stage)}: ${item.count}</span>`).join('')
        : '<p class="empty-state">Нет проектов под текущими фильтрами.</p>';

    elements.statsProjects.innerHTML = payload.projects.length
        ? payload.projects.map((project) => `
            <div class="stats-project-row">
                <strong>${escapeHtml(project.name || 'Без названия')}</strong>
                <span>${escapeHtml(project.code || '')}</span>
                <span>${escapeHtml(project.project_group || 'Без группы')}</span>
                <span>PLAN ${formatScore(project.plan_score)} / FACT ${formatScore(project.fact_score)}</span>
            </div>
        `).join('')
        : '';
}

function updateHeroScores() {
    elements.heroPlanScore.textContent = formatScore(state.currentProject?.plan_result?.total_score);
    elements.heroFactScore.textContent = formatScore(state.currentProject?.fact_result?.total_score);
}

function showMessage(message, isError = false) {
    elements.formMessage.textContent = message;
    elements.formMessage.classList.toggle('is-error', isError);
}

function formatScore(value) {
    if (value === null || value === undefined || value === '') {
        return '-';
    }
    return Number(value).toFixed(6);
}

function escapeHtml(value) {
    return String(value || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}
