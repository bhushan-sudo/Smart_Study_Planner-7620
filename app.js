// Smart Study Planner - Enhanced Dashboard with Forest Theme
// All Features: Generate Plan, Chapter Management, Interactive Calendar, Custom Timer with Sounds

const API_URL = 'http://localhost:5000/api';
let currentUser = null;
let currentToken = null;
let pomodoroTimer = null;
let charts = {};
let generatedPlan = null;
let currentSchedule = null;

// ==================== AUTHENTICATION ====================

function checkAuth() {
    const user = localStorage.getItem('user');
    const token = localStorage.getItem('token');

    if (!user || !token) {
        window.location.href = '/login';
        return false;
    }

    currentUser = JSON.parse(user);
    currentToken = token;

    const userNameEl = document.getElementById('userNameDisplay');
    const userAvatarEl = document.getElementById('userAvatar');

    if (userNameEl) {
        userNameEl.textContent = currentUser.full_name || currentUser.username;
    }

    if (userAvatarEl) {
        const initial = (currentUser.full_name || currentUser.username).charAt(0).toUpperCase();
        userAvatarEl.textContent = initial;
    }

    return true;
}

function logout() {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    window.location.href = '/login';
}

// ==================== TAB NAVIGATION ====================

function initTabNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tabName = item.dataset.tab;

            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            tabContents.forEach(tab => tab.classList.remove('active'));
            document.getElementById(`${tabName}Tab`).classList.add('active');

            localStorage.setItem('activeTab', tabName);
            loadTabData(tabName);
        });
    });

    const lastTab = localStorage.getItem('activeTab') || 'home';
    const activeNav = document.querySelector(`[data-tab="${lastTab}"]`);
    if (activeNav) {
        activeNav.click();
    } else {
        loadTabData('home');
    }
}

function loadTabData(tabName) {
    switch (tabName) {
        case 'home':
            loadHomeData();
            break;
        case 'subjects':
            loadSubjects();
            break;
        case 'plan':
            initializeCalendar();
            break;
        case 'timer':
            initializeTimer();
            break;
        case 'progress':
            initializeAnalytics();
            break;
    }
}

// ==================== HOME TAB - GENERATE PLAN ====================

async function loadHomeData() {
    try {
        const subjectsRes = await fetch(`${API_URL}/users/${currentUser.user_id}/subjects`, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });

        if (subjectsRes.ok) {
            const subjectsData = await subjectsRes.json();
            const subjectsCount = subjectsData.subjects?.length || 0;
            document.getElementById('subjectsCount').textContent = subjectsCount;
        }

        document.getElementById('sessionsCount').textContent = '1';
        document.getElementById('studyTime').textContent = '0.4h';
        document.getElementById('progressPercent').textContent = '27%';

        // Check if there's a generated plan
        checkForGeneratedPlan();
    } catch (error) {
        console.error('Error loading home data:', error);
    }
}

async function generateTodaysPlan() {
    try {
        const planDisplay = document.getElementById('planDisplay');
        const startBtn = document.getElementById('startScheduleBtn');
        const notepadArea = document.getElementById('notepadArea');

        planDisplay.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i><p>Generating Plan...</p></div>';

        const response = await fetch(`${API_URL}/users/${currentUser.user_id}/planner/schedule`, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            generatedPlan = data;

            // Enable notepad when plan is generated
            notepadArea.style.display = 'block';
            startBtn.style.display = 'inline-flex';

            displayGeneratedPlan(data);
            showToast('Plan generated successfully!', 'success');

            // Auto-load notepad content if exists
            loadNotepad();
        } else {
            planDisplay.innerHTML = '<p class="error">Failed to generate plan. Please try again.</p>';
            showToast('Failed to generate plan', 'error');
        }
    } catch (error) {
        console.error('Error generating plan:', error);
        showToast('Error generating plan', 'error');
    }
}

function displayGeneratedPlan(data) {
    const planDisplay = document.getElementById('planDisplay');
    planDisplay.classList.remove('empty-state');

    // The backend returns { schedule: { 'YYYY-MM-DD': [tasks...] } }
    const schedule = data.schedule || {};
    const today = new Date().toISOString().split('T')[0];
    const tasks = schedule[today] || [];

    if (tasks.length === 0) {
        planDisplay.innerHTML = '<p class="empty-state">No tasks scheduled for today. You might have completed everything or have a free day!</p>';
        return;
    }

    planDisplay.innerHTML = `
        <div id="todaysPlanList" style="display: flex; flex-direction: column; gap: 12px; text-align: left; width: 100%;">
            ${generatePlanHTML(tasks)}
        </div>
    `;
}

function saveNotepad() {
    const content = document.getElementById('studyNotepad').value;
    localStorage.setItem(`notepad_${currentUser.user_id}`, content);
    showToast('Notes saved!', 'success');
}

function loadNotepad() {
    const content = localStorage.getItem(`notepad_${currentUser.user_id}`);
    if (content) {
        document.getElementById('studyNotepad').value = content;
    }
}

function generatePlanHTML(tasks) {
    if (!tasks || tasks.length === 0) {
        return '<p class="empty-state">No tasks scheduled</p>';
    }

    return tasks.map((task, index) => `
        <div class="plan-item" style="background: var(--bg-card); padding: 16px; border-radius: var(--radius-md); border-left: 4px solid var(--primary); display: flex; align-items: center; gap: 12px;">
            <input type="checkbox" id="task-${task.task_id}" onchange="markTaskComplete(${task.task_id})" style="width: 20px; height: 20px; cursor: pointer;">
            <div style="flex: 1;">
                <div style="font-weight: 600; color: var(--text-primary);">${task.title}</div>
                <div style="font-size: 13px; color: var(--text-secondary); margin-top: 4px;">
                    <i class="far fa-clock"></i> ${task.estimated_hours || 1} hours • ${task.subject_name || 'General'}
                </div>
            </div>
            <span class="badge ${task.priority === 3 ? 'danger' : task.priority === 2 ? 'warning' : 'success'}">
                ${task.priority === 3 ? 'High' : task.priority === 2 ? 'Medium' : 'Low'}
            </span>
        </div>
    `).join('');
}

function startSchedule() {
    if (!generatedPlan) {
        showToast('Please generate a plan first', 'warning');
        return;
    }

    currentSchedule = {
        started: true,
        startTime: new Date(),
        currentTaskIndex: 0
    };

    showToast('Schedule started! Good luck with your studies!', 'success');

    // Highlight first task
    const firstCheckbox = document.querySelector('#todaysPlanList input[type="checkbox"]');
    if (firstCheckbox) {
        firstCheckbox.parentElement.style.background = 'var(--mint-light)';
    }
}

function markTaskComplete(taskId) {
    const checkbox = document.getElementById(`task-${taskId}`);
    if (checkbox.checked) {
        checkbox.parentElement.style.opacity = '0.6';
        checkbox.parentElement.style.textDecoration = 'line-through';
        showToast('Task completed! Great job!', 'success');
    } else {
        checkbox.parentElement.style.opacity = '1';
        checkbox.parentElement.style.textDecoration = 'none';
    }
}

function checkForGeneratedPlan() {
    // Check if plan exists in localStorage or fetch from API
    const savedPlan = localStorage.getItem('todaysPlan');
    if (savedPlan) {
        generatedPlan = JSON.parse(savedPlan);
        displayGeneratedPlan(generatedPlan);
    }
}

// ==================== SUBJECTS TAB - WITH CHAPTERS ====================

async function loadSubjects() {
    const subjectsList = document.getElementById('subjectsList');

    try {
        const response = await fetch(`${API_URL}/users/${currentUser.user_id}/subjects`, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const subjects = data.subjects || [];

        document.getElementById('subjectCountText').textContent = subjects.length;

        if (subjects.length === 0) {
            subjectsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-book-open"></i>
                    <p>No subjects yet</p>
                    <button class="btn btn-primary" onclick="showAddSubjectModal()" style="margin-top: 16px;">
                        <i class="fas fa-plus"></i> Add Your First Subject
                    </button>
                </div>
            `;
            return;
        }

        const colors = ['red', 'cyan', 'orange', 'purple', 'green'];
        const difficulties = ['easy', 'medium', 'hard'];

        subjectsList.innerHTML = subjects.map((subject, index) => {
            const color = colors[index % colors.length];
            const difficulty = difficulties[subject.priority - 1] || 'medium';
            const progress = Math.floor(Math.random() * 100);

            return `
                <div class="subject-card color-${color}">
                    <div class="subject-header">
                        <div class="subject-icon">📖</div>
                        <div class="subject-info">
                            <div class="subject-name">${subject.subject_name}</div>
                            <div class="subject-badges">
                                <span class="badge ${difficulty}">${difficulty}</span>
                                <span class="badge due"><i class="far fa-calendar"></i> Today!</span>
                            </div>
                        </div>
                        <div class="subject-actions">
                            <button class="icon-btn" onclick="editSubject(${subject.subject_id})" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="icon-btn" onclick="deleteSubject(${subject.subject_id})" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="subject-progress">
                        <span>Progress</span>
                        <span>0/10 chapters</span>
                    </div>
                    <div class="progress-bar-container">
                        <div class="progress-bar" style="width: ${progress}%"></div>
                    </div>
                    <div class="chapter-controls">
                        <button class="btn btn-sm btn-secondary" onclick="updateChapters(${subject.subject_id}, -1)">
                            <i class="fas fa-minus"></i> 1
                        </button>
                        <button class="btn btn-sm btn-primary" onclick="updateChapters(${subject.subject_id}, 1)">
                            <i class="fas fa-plus"></i> 1 Chapter
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading subjects:', error);
        subjectsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Error loading subjects</p>
            </div>
        `;
    }
}

function showAddSubjectModal() {
    document.getElementById('addSubjectModal').classList.add('active');
}

function closeAddSubjectModal() {
    document.getElementById('addSubjectModal').classList.remove('active');
    document.getElementById('addSubjectForm').reset();
}

function addSubjectInputField() {
    const container = document.getElementById('subjectInputContainer');
    const newEntry = document.createElement('div');
    newEntry.className = 'subject-entry-group';
    newEntry.style.cssText = 'padding: 20px; background: var(--bg-tertiary); border-radius: var(--radius-lg); margin-bottom: 16px; position: relative;';

    newEntry.innerHTML = `
        <button type="button" class="close-modal" onclick="this.parentElement.remove()" style="position: absolute; top: 12px; right: 12px; background: var(--danger); color: white; width: 28px; height: 28px; border-radius: 50%;">
            <i class="fas fa-times"></i>
        </button>
        <div class="form-group" style="margin-bottom: 16px;">
            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: var(--text-primary);">Subject Name</label>
            <input type="text" name="subject_name[]" required placeholder="e.g., Mathematics" style="width: 100%; padding: 10px 14px; border: 1px solid var(--border-color); background: var(--bg-secondary); color: var(--text-primary); border-radius: var(--radius-md); font-size: 14px;">
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
            <div class="form-group">
                <label style="display: block; margin-bottom: 8px; font-weight: 600; color: var(--text-primary);">Level</label>
                <input type="text" name="level[]" placeholder="e.g., Grade 10" style="width: 100%; padding: 10px 14px; border: 1px solid var(--border-color); background: var(--bg-secondary); color: var(--text-primary); border-radius: var(--radius-md); font-size: 14px;">
            </div>
            <div class="form-group">
                <label style="display: block; margin-bottom: 8px; font-weight: 600; color: var(--text-primary);">Target</label>
                <input type="text" name="target_grade[]" placeholder="e.g., A+" style="width: 100%; padding: 10px 14px; border: 1px solid var(--border-color); background: var(--bg-secondary); color: var(--text-primary); border-radius: var(--radius-md); font-size: 14px;">
            </div>
        </div>

        <div class="form-group" style="margin-bottom: 16px;">
            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: var(--text-primary);">Current Topic / Unit</label>
            <input type="text" name="current_topic[]" placeholder="e.g., Algebra" style="width: 100%; padding: 10px 14px; border: 1px solid var(--border-color); background: var(--bg-secondary); color: var(--text-primary); border-radius: var(--radius-md); font-size: 14px;">
        </div>

        <div class="form-group" style="margin-bottom: 16px;">
            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: var(--text-primary);">
                Sub Topics / Chapters
                <span style="font-size: 12px; color: var(--text-secondary); font-weight: 400;">(one per line)</span>
            </label>
            <div class="topics-list" style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px;">
                <div style="display: flex; gap: 8px; align-items: center;">
                    <input type="text" class="topic-input" placeholder="e.g., Linear Equations" style="flex: 1; padding: 8px 12px; border: 1px solid var(--border-color); background: var(--bg-secondary); color: var(--text-primary); border-radius: var(--radius-sm); font-size: 13px;">
                    <button type="button" onclick="this.parentElement.remove()" style="padding: 8px 12px; background: transparent; border: 1px solid var(--border-color); color: var(--text-secondary); border-radius: var(--radius-sm); cursor: pointer; display: none;">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            <button type="button" onclick="addTopicField(this)" style="padding: 8px 16px; background: var(--bg-secondary); border: 1px solid var(--border-color); color: var(--text-secondary); border-radius: var(--radius-md); cursor: pointer; font-size: 13px; transition: var(--transition);">
                <i class="fas fa-plus"></i> Add Sub Topic
            </button>
        </div>
        <div class="form-group">
            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: var(--text-primary);">Priority</label>
            <select name="priority[]" required style="width: 100%; padding: 10px 14px; border: 1px solid var(--border-color); background: var(--bg-secondary); color: var(--text-primary); border-radius: var(--radius-md); font-size: 14px;">
                <option value="1">Low</option>
                <option value="2" selected>Medium</option>
                <option value="3">High</option>
            </select>
        </div>
    `;
    container.appendChild(newEntry);
}

function addTopicField(button) {
    const topicsList = button.previousElementSibling;
    const newTopicEntry = document.createElement('div');
    newTopicEntry.style.cssText = 'display: flex; gap: 8px; align-items: center;';

    newTopicEntry.innerHTML = `
        <input type="text" class="topic-input" placeholder="e.g., Geometry" style="flex: 1; padding: 8px 12px; border: 1px solid var(--border-color); background: var(--bg-secondary); color: var(--text-primary); border-radius: var(--radius-sm); font-size: 13px;">
        <button type="button" onclick="this.parentElement.remove()" style="padding: 8px 12px; background: transparent; border: 1px solid var(--border-color); color: var(--text-secondary); border-radius: var(--radius-sm); cursor: pointer;">
            <i class="fas fa-times"></i>
        </button>
    `;

    topicsList.appendChild(newTopicEntry);
    // Focus on the new input
    newTopicEntry.querySelector('.topic-input').focus();
}

async function handleAddSubjects(event) {
    event.preventDefault();

    // Get all subject entry groups
    const subjectGroups = document.querySelectorAll('.subject-entry-group');
    const color = document.querySelector('input[name="color"]:checked').value;

    try {
        let successCount = 0;

        for (const group of subjectGroups) {
            // Get subject name
            const subjectName = group.querySelector('input[name="subject_name[]"]').value.trim();

            // Get all topics for this subject
            const topicInputs = group.querySelectorAll('.topic-input');
            const topics = Array.from(topicInputs)
                .map(input => input.value.trim())
                .filter(topic => topic.length > 0); // Remove empty topics

            // Get priority
            const priority = parseInt(group.querySelector('select[name="priority[]"]').value);

            // Get new fields
            const level = group.querySelector('input[name="level[]"]').value.trim();
            const targetGrade = group.querySelector('input[name="target_grade[]"]').value.trim();
            const currentTopic = group.querySelector('input[name="current_topic[]"]').value.trim();

            // Send to API
            const response = await fetch(`${API_URL}/users/${currentUser.user_id}/subjects`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${currentToken}`
                },
                body: JSON.stringify({
                    subject_name: subjectName,
                    priority: priority,
                    color_code: color,
                    level: level,
                    target_grade: targetGrade,
                    current_topic: currentTopic,
                    sub_topics: topics.join(', ')
                })
            });

            if (response.ok) {
                successCount++;

                // If topics were provided, create chapters for this subject
                if (topics.length > 0) {
                    const subjectData = await response.json();
                    const subjectId = subjectData.subject_id || subjectData.id;

                    // Create chapters for each topic
                    for (let i = 0; i < topics.length; i++) {
                        await fetch(`${API_URL}/subjects/${subjectId}/chapters`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${currentToken}`
                            },
                            body: JSON.stringify({
                                chapter_name: topics[i],
                                chapter_number: i + 1,
                                estimated_hours: 2 // Default estimate
                            })
                        });
                    }
                }
            }
        }

        if (successCount > 0) {
            showToast(`${successCount} subject(s) added successfully!`, 'success');
            closeAddSubjectModal();
            loadSubjects();
        } else {
            showToast('Failed to add subjects', 'error');
        }
    } catch (error) {
        console.error('Error adding subjects:', error);
        showToast('Error adding subjects', 'error');
    }
}

function showEditSubjectModal(subject) {
    document.getElementById('editSubjectId').value = subject.subject_id;
    document.getElementById('editSubjectName').value = subject.subject_name;
    document.getElementById('editSubjectPriority').value = subject.priority;
    document.getElementById('editSubjectModal').classList.add('active');
}

function closeEditSubjectModal() {
    document.getElementById('editSubjectModal').classList.remove('active');
    document.getElementById('editSubjectForm').reset();
}

async function editSubject(id) {
    try {
        const response = await fetch(`${API_URL}/subjects/${id}`, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            showEditSubjectModal(data.subject);
        } else {
            showToast('Failed to load subject details', 'error');
        }
    } catch (error) {
        console.error('Error loading subject:', error);
        showToast('Error loading subject', 'error');
    }
}

async function handleEditSubject(event) {
    event.preventDefault();
    const id = document.getElementById('editSubjectId').value;
    const name = document.getElementById('editSubjectName').value;
    const priority = document.getElementById('editSubjectPriority').value;

    try {
        const response = await fetch(`${API_URL}/subjects/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({
                subject_name: name,
                priority: parseInt(priority)
            })
        });

        if (response.ok) {
            showToast('Subject updated successfully!', 'success');
            closeEditSubjectModal();
            loadSubjects();
        } else {
            showToast('Failed to update subject', 'error');
        }
    } catch (error) {
        console.error('Error updating subject:', error);
        showToast('Error updating subject', 'error');
    }
}

async function deleteSubject(id) {
    if (!confirm('Are you sure you want to delete this subject? All related tasks will be affected.')) return;

    try {
        const response = await fetch(`${API_URL}/subjects/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });

        if (response.ok) {
            showToast('Subject deleted successfully', 'success');
            loadSubjects();
        } else {
            showToast('Failed to delete subject', 'error');
        }
    } catch (error) {
        console.error('Error deleting subject:', error);
        showToast('Error deleting subject', 'error');
    }
}

function updateChapters(subjectId, delta) {
    // Local state for now as backend doesn't have chapters_completed column yet
    showToast(`Chapter progress updated (Subject ${subjectId})`, 'success');
    // In a real app, this would update the database via an API call
}


// ==================== CALENDAR (PLAN TAB) - INTERACTIVE ====================

let currentCalendarDate = new Date();
let calendarTasks = {};

function initializeCalendar() {
    const planTab = document.getElementById('planTab');

    planTab.innerHTML = `
        <div class="section">
            <div class="calendar-header">
                <h2 class="section-title">
                    <i class="fas fa-calendar-alt"></i>
                    <span id="currentMonth"></span>
                </h2>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-secondary btn-sm" onclick="previousMonth()">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="todayMonth()">Today</button>
                    <button class="btn btn-secondary btn-sm" onclick="nextMonth()">
                        <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>
            <div class="calendar-grid" id="calendarGrid"></div>
        </div>
    `;

    loadCalendarTasks();
    renderCalendar();
}

async function loadCalendarTasks() {
    try {
        const response = await fetch(`${API_URL}/users/${currentUser.user_id}/tasks`, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            const tasks = data.tasks || [];

            // Group tasks by date
            calendarTasks = {};
            tasks.forEach(task => {
                const taskDate = task.scheduled_date || task.deadline;
                if (taskDate) {
                    const date = new Date(taskDate).toDateString();
                    if (!calendarTasks[date]) {
                        calendarTasks[date] = [];
                    }
                    calendarTasks[date].push(task);
                }
            });
            renderCalendar(); // Re-render once data is loaded
        }
    } catch (error) {
        console.error('Error loading calendar tasks:', error);
    }
}

function renderCalendar() {
    const year = currentCalendarDate.getFullYear();
    const month = currentCalendarDate.getMonth();

    document.getElementById('currentMonth').textContent =
        currentCalendarDate.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });

    const grid = document.getElementById('calendarGrid');
    grid.innerHTML = '';

    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    days.forEach(day => {
        const header = document.createElement('div');
        header.className = 'calendar-day-header';
        header.textContent = day;
        grid.appendChild(header);
    });

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());

    for (let i = 0; i < 42; i++) {
        const date = new Date(startDate);
        date.setDate(startDate.getDate() + i);

        const dayEl = document.createElement('div');
        dayEl.className = 'calendar-day';
        dayEl.textContent = date.getDate();

        if (date.getMonth() !== month) {
            dayEl.classList.add('other-month');
        }

        const today = new Date();
        if (date.toDateString() === today.toDateString()) {
            dayEl.classList.add('today');
        }

        // Check for tasks on this date
        const dateStr = date.toDateString();
        if (calendarTasks[dateStr]) {
            const tasks = calendarTasks[dateStr];
            const completedTasks = tasks.filter(t => t.status === 'completed').length;

            // Add indicator
            const indicator = document.createElement('div');
            indicator.style.cssText = `
                position: absolute;
                bottom: 4px;
                left: 50%;
                transform: translateX(-50%);
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: ${completedTasks === tasks.length ? 'var(--success)' :
                    completedTasks > 0 ? 'var(--warning)' : 'var(--danger)'};
            `;
            dayEl.style.position = 'relative';
            dayEl.appendChild(indicator);

            // Make clickable
            dayEl.style.cursor = 'pointer';
            dayEl.addEventListener('click', () => showDateTasks(date, tasks));
        }

        grid.appendChild(dayEl);
    }
}

function showDateTasks(date, tasks) {
    const dateStr = date.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

    const tasksHTML = tasks.map(task => `
        <div style="padding: 12px; background: var(--bg-card); border-radius: var(--radius-sm); margin-bottom: 8px; border-left: 4px solid ${task.status === 'completed' ? 'var(--success)' : 'var(--warning)'};">
            <div style="font-weight: 600; color: var(--text-primary);">${task.title}</div>
            <div style="font-size: 13px; color: var(--text-secondary); margin-top: 4px;">
                <i class="far fa-clock"></i> ${task.estimated_hours || 1}h • ${task.subject_name || 'General'}
            </div>
            <div style="font-size: 12px; margin-top: 4px;">
                Status: <span class="badge ${task.status === 'completed' ? 'success' : 'warning'}">${task.status}</span>
            </div>
        </div>
    `).join('');

    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.style.zIndex = '2000';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 400px; animation: slideIn 0.3s ease-out;">
            <div class="modal-header">
                <h3>Tasks for ${date.getDate()} ${date.toLocaleString('default', { month: 'short' })}</h3>
                <button class="icon-btn" onclick="this.closest('.modal').remove()"><i class="fas fa-times"></i></button>
            </div>
            <div style="margin-top: 15px; max-height: 400px; overflow-y: auto;">
                ${tasksHTML || '<p style="text-align: center; color: var(--text-secondary);">No tasks for this day</p>'}
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function previousMonth() {
    currentCalendarDate.setMonth(currentCalendarDate.getMonth() - 1);
    renderCalendar();
}

function nextMonth() {
    currentCalendarDate.setMonth(currentCalendarDate.getMonth() + 1);
    renderCalendar();
}

function todayMonth() {
    currentCalendarDate = new Date();
    renderCalendar();
}

// ==================== POMODORO TIMER - CUSTOM WITH SOUNDS ====================

class PomodoroTimer {
    constructor() {
        this.workDuration = 25 * 60;
        this.breakDuration = 5 * 60;
        this.timeLeft = this.workDuration;
        this.isRunning = false;
        this.isBreak = false;
        this.interval = null;
        this.soundEnabled = true;

        // Simple beep sounds using Web Audio API
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }

    playSound(type) {
        if (!this.soundEnabled) return;

        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);

        if (type === 'start') {
            oscillator.frequency.value = 800;
            gainNode.gain.setValueAtTime(0.3, this.audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.1);
            oscillator.start(this.audioContext.currentTime);
            oscillator.stop(this.audioContext.currentTime + 0.1);
        } else if (type === 'stop') {
            oscillator.frequency.value = 400;
            gainNode.gain.setValueAtTime(0.3, this.audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.15);
            oscillator.start(this.audioContext.currentTime);
            oscillator.stop(this.audioContext.currentTime + 0.15);
        } else if (type === 'complete') {
            // Play two beeps
            for (let i = 0; i < 2; i++) {
                const osc = this.audioContext.createOscillator();
                const gain = this.audioContext.createGain();
                osc.connect(gain);
                gain.connect(this.audioContext.destination);
                osc.frequency.value = 1000;
                gain.gain.setValueAtTime(0.3, this.audioContext.currentTime + i * 0.2);
                gain.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + i * 0.2 + 0.2);
                osc.start(this.audioContext.currentTime + i * 0.2);
                osc.stop(this.audioContext.currentTime + i * 0.2 + 0.2);
            }
        }
    }

    setCustomDuration(work, breakTime) {
        this.workDuration = work * 60;
        this.breakDuration = breakTime * 60;
        if (!this.isRunning) {
            this.timeLeft = this.isBreak ? this.breakDuration : this.workDuration;
            this.updateDisplay();
        }
    }

    toggleSound() {
        this.soundEnabled = !this.soundEnabled;
        showToast(`Sound ${this.soundEnabled ? 'enabled' : 'disabled'}`, 'info');
    }

    start() {
        if (this.isRunning) return;

        this.isRunning = true;
        this.playSound('start');
        this.updateButtons();

        this.interval = setInterval(() => {
            this.timeLeft--;
            this.updateDisplay();

            if (this.timeLeft <= 0) {
                this.complete();
            }
        }, 1000);
    }

    pause() {
        this.isRunning = false;
        this.playSound('stop');
        clearInterval(this.interval);
        this.updateButtons();
    }

    reset() {
        this.pause();
        this.isBreak = false;
        this.timeLeft = this.workDuration;
        this.updateDisplay();
        this.updateLabel();
    }

    complete() {
        this.pause();
        this.playSound('complete');

        if (this.isBreak) {
            this.isBreak = false;
            this.timeLeft = this.workDuration;
            showToast('Break complete! Time to focus.', 'success');
        } else {
            this.isBreak = true;
            this.timeLeft = this.breakDuration;
            showToast('Great work! Take a break.', 'success');
        }

        this.updateDisplay();
        this.updateLabel();
    }

    updateDisplay() {
        const minutes = Math.floor(this.timeLeft / 60);
        const seconds = this.timeLeft % 60;
        const display = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

        const displayEl = document.getElementById('timerDisplay');
        if (displayEl) {
            displayEl.textContent = display;
        }
    }

    updateLabel() {
        const labelEl = document.getElementById('timerLabel');
        if (labelEl) {
            labelEl.textContent = this.isBreak ? 'Break Time' : 'Focus Session';
        }
    }

    updateButtons() {
        const startBtn = document.getElementById('timerStart');
        const pauseBtn = document.getElementById('timerPause');

        if (startBtn && pauseBtn) {
            if (this.isRunning) {
                startBtn.style.display = 'none';
                pauseBtn.style.display = 'inline-flex';
            } else {
                startBtn.style.display = 'inline-flex';
                pauseBtn.style.display = 'none';
            }
        }
    }
}

function initializeTimer() {
    const timerTab = document.getElementById('timerTab');

    timerTab.innerHTML = `
        <div class="section">
            <div class="timer-container">
                <h2 class="section-title" style="justify-content: center;">
                    <i class="fas fa-stopwatch"></i>
                    Pomodoro Timer
                </h2>
                
                <!-- Timer Settings -->
                <div class="timer-settings" style="background: var(--bg-card); padding: 20px; border-radius: var(--radius-md); margin: 20px 0;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: var(--text-secondary);">Work (min)</label>
                            <input type="number" id="workDuration" value="25" min="1" max="120" 
                                   style="width: 100%; padding: 8px; border: 1px solid var(--border-color); border-radius: var(--radius-sm);"
                                   onchange="updateTimerDuration()">
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: var(--text-secondary);">Break (min)</label>
                            <input type="number" id="breakDuration" value="5" min="1" max="30"
                                   style="width: 100%; padding: 8px; border: 1px solid var(--border-color); border-radius: var(--radius-sm);"
                                   onchange="updateTimerDuration()">
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 8px; margin-bottom: 16px;">
                        <button class="btn btn-sm btn-secondary" onclick="setPreset(15, 3)">Quick (15/3)</button>
                        <button class="btn btn-sm btn-secondary" onclick="setPreset(25, 5)">Pomodoro (25/5)</button>
                        <button class="btn btn-sm btn-secondary" onclick="setPreset(50, 10)">Long (50/10)</button>
                    </div>
                    
                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                        <input type="checkbox" id="soundEnabled" checked onchange="pomodoroTimer.toggleSound()"
                               style="width: 18px; height: 18px; cursor: pointer;">
                        <span style="font-weight: 500;">Enable Sounds</span>
                    </label>
                </div>
                
                <div class="timer-label" id="timerLabel">Focus Session</div>
                <div class="timer-display" id="timerDisplay">25:00</div>
                <div class="timer-controls">
                    <button class="btn btn-primary" id="timerStart" onclick="pomodoroTimer.start()">
                        <i class="fas fa-play"></i> Start
                    </button>
                    <button class="btn btn-secondary" id="timerPause" onclick="pomodoroTimer.pause()" style="display: none;">
                        <i class="fas fa-pause"></i> Pause
                    </button>
                    <button class="btn btn-secondary" onclick="pomodoroTimer.reset()">
                        <i class="fas fa-redo"></i> Reset
                    </button>
                </div>
                <p style="margin-top: 30px; color: var(--text-secondary); font-size: 14px; text-align: center;">
                    <i class="fas fa-info-circle"></i> Customize your timer duration above
                </p>
            </div>
        </div>
    `;

    if (!pomodoroTimer) {
        pomodoroTimer = new PomodoroTimer();
    }
    pomodoroTimer.updateDisplay();
    pomodoroTimer.updateLabel();
    pomodoroTimer.updateButtons();
}

function updateTimerDuration() {
    const work = parseInt(document.getElementById('workDuration').value);
    const breakTime = parseInt(document.getElementById('breakDuration').value);
    pomodoroTimer.setCustomDuration(work, breakTime);
    showToast(`Timer updated: ${work}/${breakTime} minutes`, 'success');
}

function setPreset(work, breakTime) {
    document.getElementById('workDuration').value = work;
    document.getElementById('breakDuration').value = breakTime;
    pomodoroTimer.setCustomDuration(work, breakTime);
    showToast(`Preset applied: ${work}/${breakTime} minutes`, 'success');
}

// ==================== ANALYTICS (PROGRESS TAB) ====================

function initializeAnalytics() {
    const progressTab = document.getElementById('progressTab');

    progressTab.innerHTML = `
        <div class="section">
            <h2 class="section-title">
                <i class="fas fa-chart-pie"></i>
                Analytics & Progress
            </h2>
            <div class="charts-grid">
                <div class="chart-card">
                    <div class="chart-title">Weekly Study Hours</div>
                    <div class="chart-container">
                        <canvas id="weeklyChart"></canvas>
                    </div>
                </div>
                <div class="chart-card">
                    <div class="chart-title">Subject Distribution</div>
                    <div class="chart-container">
                        <canvas id="subjectChart"></canvas>
                    </div>
                </div>
                <div class="chart-card">
                    <div class="chart-title">Focus Sessions</div>
                    <div class="chart-container">
                        <canvas id="sessionsChart"></canvas>
                    </div>
                </div>
                <div class="chart-card">
                    <div class="chart-title">Progress Trend</div>
                    <div class="chart-container">
                        <canvas id="progressChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    `;

    createCharts();
}

function createCharts() {
    const weeklyCtx = document.getElementById('weeklyChart');
    if (weeklyCtx && typeof Chart !== 'undefined') {
        charts.weekly = new Chart(weeklyCtx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Hours',
                    data: [2, 3, 1.5, 4, 2.5, 1, 0.5],
                    borderColor: '#2d5016',
                    backgroundColor: 'rgba(45, 80, 22, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }

    const subjectCtx = document.getElementById('subjectChart');
    if (subjectCtx && typeof Chart !== 'undefined') {
        charts.subject = new Chart(subjectCtx, {
            type: 'doughnut',
            data: {
                labels: ['Mathematics', 'Physics', 'Chemistry'],
                datasets: [{
                    data: [40, 35, 25],
                    backgroundColor: ['#bc8f8f', '#8b7355', '#d4a5a5']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }

    const sessionsCtx = document.getElementById('sessionsChart');
    if (sessionsCtx && typeof Chart !== 'undefined') {
        charts.sessions = new Chart(sessionsCtx, {
            type: 'bar',
            data: {
                labels: ['Morning', 'Afternoon', 'Evening', 'Night'],
                datasets: [{
                    label: 'Sessions',
                    data: [3, 5, 4, 1],
                    backgroundColor: '#bc8f8f'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
            }
        });
    }

    const progressCtx = document.getElementById('progressChart');
    if (progressCtx && typeof Chart !== 'undefined') {
        charts.progress = new Chart(progressCtx, {
            type: 'line',
            data: {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                datasets: [{
                    label: 'Progress %',
                    data: [15, 35, 60, 75],
                    borderColor: '#bc8f8f',
                    backgroundColor: 'rgba(188, 143, 143, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, max: 100 } }
            }
        });
    }
}

// ==================== TOAST NOTIFICATIONS ====================

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'toast';

    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };

    const colors = {
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#bc8f8f'
    };

    toast.innerHTML = `
        <i class="fas ${icons[type]}" style="color: ${colors[type]}"></i>
        <span>${message}</span>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', function () {
    document.head.appendChild(style);

    if (checkAuth()) {
        initTabNavigation();

        // Add Generate Plan button handler
        setTimeout(() => {
            const generateBtn = document.querySelector('#homeTab button[onclick*="Generate"]');
            if (generateBtn) {
                generateBtn.onclick = generateTodaysPlan;
            }
        }, 1000);
    }
});
