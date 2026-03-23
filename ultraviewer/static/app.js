const { createApp } = Vue;

const app = createApp({
    data() {
        return {
            tabs: [],
            activeTabId: null,
            suites: [],
            selectedNode: null,
            selectedSuiteData: null,
            selectedLeafResult: null,
            isRunning: false,
            runProgress: null,
            showCreateSuite: false,
            newSuiteName: '',
            newSuitePath: '',
        };
    },
    async mounted() {
        await this.loadTabs();
        if (this.tabs.length === 0) {
            await this.createTab('Default');
        }
    },
    watch: {
        activeTabId() {
            this.selectedNode = null;
            this.selectedSuiteData = null;
            this.selectedLeafResult = null;
            this.loadSuites();
        },
    },
    methods: {
        // --- Tabs ---
        async loadTabs() {
            const resp = await fetch('/api/tabs');
            this.tabs = await resp.json();
            if (this.tabs.length > 0 && !this.activeTabId) {
                this.activeTabId = this.tabs[0].id;
            }
        },
        selectTab(id) {
            this.activeTabId = id;
        },
        async createTab(name) {
            const tabName = name || 'New Tab';
            const resp = await fetch('/api/tabs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: tabName, position: this.tabs.length }),
            });
            const tab = await resp.json();
            this.tabs.push(tab);
            this.activeTabId = tab.id;
        },
        async renameTab({ id, name }) {
            await fetch(`/api/tabs/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name }),
            });
            const tab = this.tabs.find(t => t.id === id);
            if (tab) tab.name = name;
        },
        async deleteTab(id) {
            await fetch(`/api/tabs/${id}`, { method: 'DELETE' });
            this.tabs = this.tabs.filter(t => t.id !== id);
            if (this.activeTabId === id) {
                this.activeTabId = this.tabs.length > 0 ? this.tabs[0].id : null;
            }
        },

        // --- Suites ---
        async loadSuites() {
            if (!this.activeTabId) { this.suites = []; return; }
            const resp = await fetch(`/api/tabs/${this.activeTabId}/suites`);
            this.suites = await resp.json();
        },
        createSuiteDialog() {
            this.newSuiteName = '';
            this.newSuitePath = '';
            this.showCreateSuite = true;
        },
        async createSuite() {
            if (!this.newSuiteName.trim() || !this.newSuitePath.trim()) return;
            await fetch(`/api/tabs/${this.activeTabId}/suites`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: this.newSuiteName,
                    folder_path: this.newSuitePath,
                    position: this.suites.length,
                }),
            });
            this.showCreateSuite = false;
            await this.loadSuites();
        },
        selectSuite(suite) {
            this.selectedNode = { type: 'suite', id: suite.id };
            this.selectedSuiteData = suite;
            this.selectedLeafResult = null;
        },
        async selectLeaf({ suite, leaf }) {
            this.selectedNode = { type: 'leaf', id: leaf.path, leaf, suite };
            this.selectedSuiteData = suite;
            this.selectedLeafResult = null;
            try {
                const resp = await fetch(`/api/suites/${suite.id}/results/${leaf.name}`);
                if (resp.ok) {
                    this.selectedLeafResult = await resp.json();
                }
            } catch {}
        },
        async saveSuiteSettings(data) {
            await fetch(`/api/suites/${data.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            await this.loadSuites();
            const updated = this.suites.find(s => s.id === data.id);
            if (updated) this.selectedSuiteData = updated;
        },

        // --- Execution ---
        async runSuite(suite) {
            this.isRunning = true;
            this.runProgress = { done: 0, total: 0 };
            try {
                const ws = new WebSocket(`ws://${location.host}/ws/execution/${suite.id}`);
                ws.onmessage = (e) => {
                    const data = JSON.parse(e.data);
                    if (data.event === 'run_started') {
                        this.runProgress = { done: 0, total: data.total };
                    } else if (data.event === 'leaf_completed' || data.event === 'leaf_error') {
                        this.runProgress.done++;
                    } else if (data.event === 'run_completed') {
                        this.isRunning = false;
                        ws.close();
                        this.loadSuites();
                    }
                };
                ws.onerror = () => { this.isRunning = false; };
                ws.onclose = () => { this.isRunning = false; };
            } catch {
                await fetch(`/api/suites/${suite.id}/run`, { method: 'POST' });
                this.isRunning = false;
                await this.loadSuites();
            }
        },
        async runLeaf({ suite, leaf }) {
            this.isRunning = true;
            try {
                const resp = await fetch(`/api/suites/${suite.id}/run/${leaf.name}`, { method: 'POST' });
                const result = await resp.json();
                this.selectedLeafResult = result;
            } catch {}
            this.isRunning = false;
        },
        async testScript(suiteId) {
            try {
                const resp = await fetch(`/api/suites/${suiteId}/test-script`, { method: 'POST' });
                const result = await resp.json();
                alert(result.status === 'success'
                    ? 'Script test passed!\n\n' + JSON.stringify(result.result, null, 2)
                    : 'Script test failed:\n\n' + (result.error_message || 'Unknown error'));
            } catch (e) {
                alert('Error testing script: ' + e.message);
            }
        },
    },
});

// Register components
app.component('tab-bar', TabBar);
app.component('tree-view', TreeView);
app.component('content-panel', ContentPanel);
app.component('suite-settings', SuiteSettings);
app.component('table-renderer', TableRenderer);
app.component('diff-renderer', DiffRenderer);
app.component('html-renderer', HtmlRenderer);
app.component('sections-renderer', SectionsRenderer);

app.mount('#app');
