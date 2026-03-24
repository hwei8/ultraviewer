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
            suiteLeaves: null,
            suiteResults: null,
            loadError: null,
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
            this.suiteLeaves = null;
            this.suiteResults = null;
            this.loadError = null;
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
        async deleteSuite(suite) {
            try {
                const resp = await fetch(`/api/suites/${suite.id}`, { method: 'DELETE' });
                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    alert('Failed to delete suite: ' + (err.detail || resp.status));
                    return;
                }
            } catch (e) {
                alert('Error deleting suite: ' + e.message);
                return;
            }
            // Clear selection if deleted suite was selected
            if (this.selectedSuiteData?.id === suite.id) {
                this.selectedNode = null;
                this.selectedSuiteData = null;
                this.selectedLeafResult = null;
                this.suiteLeaves = null;
                this.suiteResults = null;
                this.loadError = null;
            }
            await this.loadSuites();
        },
        async selectSuite(suite) {
            this.selectedNode = { type: 'suite', id: suite.id };
            this.selectedSuiteData = suite;
            this.selectedLeafResult = null;
            this.suiteLeaves = null;
            this.suiteResults = null;
            this.loadError = null;
            await this.loadSuiteLeaves(suite);
            await this.loadSuiteResults(suite);
        },
        async loadSuiteLeaves(suite) {
            try {
                const resp = await fetch(`/api/suites/${suite.id}/leaves`);
                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    this.loadError = err.detail || `Failed to load leaves (${resp.status})`;
                    this.suiteLeaves = [];
                    return;
                }
                this.suiteLeaves = await resp.json();
            } catch (e) {
                this.loadError = 'Network error loading leaves: ' + e.message;
                this.suiteLeaves = [];
            }
        },
        async loadSuiteResults(suite) {
            try {
                const resp = await fetch(`/api/suites/${suite.id}/results`);
                if (resp.ok) {
                    this.suiteResults = await resp.json();
                } else {
                    this.suiteResults = [];
                }
            } catch {
                this.suiteResults = [];
            }
        },
        async selectLeaf(payload) {
            if (!payload) {
                // Back to suite list view
                if (this.selectedSuiteData) {
                    this.selectedNode = { type: 'suite', id: this.selectedSuiteData.id };
                    this.selectedLeafResult = null;
                }
                return;
            }
            const { suite, leaf } = payload;
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
            if (updated) {
                this.selectedSuiteData = updated;
                // Reload leaves in case folder_path changed
                await this.loadSuiteLeaves(updated);
            }
        },

        // --- Execution ---
        async runSelectedLeaves({ suite, leafNames }) {
            this.isRunning = true;
            this.runProgress = { done: 0, total: leafNames.length };
            try {
                const resp = await fetch(`/api/suites/${suite.id}/run-selected`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(leafNames),
                });
                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    this.loadError = err.detail || `Run failed (${resp.status})`;
                    this.isRunning = false;
                    return;
                }
                const data = await resp.json();
                this.runProgress = { done: data.total, total: data.total };

                // Show summary
                if (data.failed > 0 || data.errors > 0) {
                    this.loadError = `Completed: ${data.passed} passed, ${data.failed} failed, ${data.errors} timed out`;
                } else {
                    this.loadError = null;
                }
            } catch (e) {
                this.loadError = 'Run failed: ' + e.message;
            }
            this.isRunning = false;
            // Reload results
            await this.loadSuiteResults(suite);
        },
        async runSuite(suite) {
            // Called from tree context menu - run all leaves
            this.isRunning = true;
            this.runProgress = { done: 0, total: 0 };
            try {
                const resp = await fetch(`/api/suites/${suite.id}/run`, { method: 'POST' });
                if (resp.ok) {
                    const data = await resp.json();
                    this.runProgress = { done: data.total, total: data.total };
                }
            } catch {}
            this.isRunning = false;
            if (this.selectedSuiteData?.id === suite.id) {
                await this.loadSuiteResults(suite);
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
            if (this.selectedSuiteData?.id === suite.id) {
                await this.loadSuiteResults(suite);
            }
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
app.component('folder-browser', FolderBrowser);
app.component('table-renderer', TableRenderer);
app.component('diff-renderer', DiffRenderer);
app.component('html-renderer', HtmlRenderer);
app.component('sections-renderer', SectionsRenderer);

app.mount('#app');
