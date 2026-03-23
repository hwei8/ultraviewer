const ContentPanel = {
    props: ['selectedNode', 'suiteData', 'leafResult', 'running', 'progress',
            'suiteLeaves', 'suiteResults', 'loadError'],
    emits: ['saveSettings', 'runSelected', 'testScript', 'selectLeaf'],
    data() {
        return {
            viewMode: 'leaves', // 'leaves' or 'config'
            selectedLeaves: {},
        };
    },
    computed: {
        renderData() {
            if (!this.leafResult || !this.leafResult.result_json) return null;
            const result = this.leafResult.result_json;
            if (typeof result === 'string') {
                try { return JSON.parse(result); } catch { return null; }
            }
            return result;
        },
        renderMode() {
            if (!this.suiteData?.rendering) return 'auto';
            return this.suiteData.rendering.render_mode || 'auto';
        },
        effectiveType() {
            if (this.renderMode !== 'auto') return this.renderMode;
            return this.renderData?.type || 'table';
        },
        allChecked() {
            if (!this.suiteLeaves || this.suiteLeaves.length === 0) return false;
            return this.suiteLeaves.every(l => this.selectedLeaves[l.name]);
        },
        someChecked() {
            if (!this.suiteLeaves) return false;
            const checked = this.suiteLeaves.filter(l => this.selectedLeaves[l.name]);
            return checked.length > 0 && checked.length < this.suiteLeaves.length;
        },
        checkedCount() {
            if (!this.suiteLeaves) return 0;
            return this.suiteLeaves.filter(l => this.selectedLeaves[l.name]).length;
        },
        checkedNames() {
            return Object.keys(this.selectedLeaves).filter(k => this.selectedLeaves[k]);
        },
        resultsByLeaf() {
            const map = {};
            if (this.suiteResults) {
                for (const r of this.suiteResults) {
                    map[r.leaf_name] = r;
                }
            }
            return map;
        },
        hasScript() {
            return this.suiteData?.script?.script_path;
        },
    },
    watch: {
        selectedNode: {
            handler(newVal, oldVal) {
                // Reset to leaves view when selecting a different suite
                if (newVal?.type === 'suite') {
                    if (!oldVal || oldVal.type !== 'suite' || oldVal.id !== newVal.id) {
                        this.viewMode = 'leaves';
                        this.selectAll();
                    }
                }
            },
            deep: true,
        },
        suiteLeaves: {
            handler() {
                // Select all leaves by default when leaves load
                this.selectAll();
            },
        },
    },
    methods: {
        toggleAll() {
            if (this.allChecked) {
                this.selectedLeaves = {};
            } else {
                this.selectAll();
            }
        },
        selectAll() {
            const sel = {};
            if (this.suiteLeaves) {
                for (const l of this.suiteLeaves) {
                    sel[l.name] = true;
                }
            }
            this.selectedLeaves = sel;
        },
        toggleLeaf(name) {
            this.selectedLeaves = {
                ...this.selectedLeaves,
                [name]: !this.selectedLeaves[name],
            };
        },
        runSelected() {
            if (this.checkedCount === 0) return;
            this.$emit('runSelected', {
                suite: this.suiteData,
                leafNames: this.checkedNames,
            });
        },
        statusIcon(leafName) {
            const r = this.resultsByLeaf[leafName];
            if (!r) return '';
            if (r.status === 'success') return '\u2705';
            if (r.status === 'error') return '\u274C';
            if (r.status === 'timeout') return '\u26A0\uFE0F';
            return '';
        },
        statusClass(leafName) {
            const r = this.resultsByLeaf[leafName];
            if (!r) return '';
            if (r.status === 'success') return 'status-pass';
            if (r.status === 'error') return 'status-error';
            if (r.status === 'timeout') return 'status-timeout';
            return '';
        },
    },
    template: `
        <div class="content-panel">
            <!-- Nothing selected -->
            <div v-if="!selectedNode" style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-secondary);">
                Select a suite or folder from the tree
            </div>

            <!-- Suite selected -->
            <template v-else-if="selectedNode.type === 'suite' && suiteData">

                <!-- Config view -->
                <template v-if="viewMode === 'config'">
                    <div class="content-header">
                        <h2>{{ suiteData.name }} - Settings</h2>
                        <button class="btn btn-secondary" @click="viewMode = 'leaves'">Back to Leaves</button>
                    </div>
                    <suite-settings
                        :suite="suiteData"
                        @save="$emit('saveSettings', $event)"
                        @test-script="$emit('testScript', $event)"
                    ></suite-settings>
                </template>

                <!-- Leaves view (default) -->
                <template v-else>
                    <div class="content-header">
                        <h2>{{ suiteData.name }}</h2>
                        <div style="display: flex; gap: 0.5rem;">
                            <button class="btn btn-secondary" @click="viewMode = 'config'">Config</button>
                            <button class="btn btn-primary" @click="runSelected"
                                    :disabled="running || checkedCount === 0 || !hasScript"
                                    :title="!hasScript ? 'No script configured - click Config to set up' : checkedCount === 0 ? 'Select at least one leaf' : 'Run ' + checkedCount + ' selected'">
                                {{ running ? 'Running...' : 'Run (' + checkedCount + ')' }}
                            </button>
                        </div>
                    </div>

                    <!-- Error banner -->
                    <div v-if="loadError" style="background: rgba(239,68,68,0.1); padding: 0.8rem 1rem; border-radius: 4px; margin-bottom: 1rem; font-size: 0.85rem;">
                        <strong class="status-error">Error:</strong> {{ loadError }}
                    </div>

                    <!-- No script warning -->
                    <div v-if="!hasScript" style="background: rgba(245,158,11,0.1); padding: 0.8rem 1rem; border-radius: 4px; margin-bottom: 1rem; font-size: 0.85rem;">
                        <strong class="status-timeout">No script configured.</strong> Click <strong>Config</strong> to set up an interpreter and script path before running.
                    </div>

                    <!-- Progress bar -->
                    <div v-if="running && progress" style="margin-bottom: 1rem;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.3rem;">
                            <span><span class="spinner"></span> Running...</span>
                            <span>{{ progress.done }} / {{ progress.total }}</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" :style="{ width: (progress.total ? progress.done / progress.total * 100 : 0) + '%' }"></div>
                        </div>
                    </div>

                    <!-- Leaf list with checkboxes -->
                    <table class="data-table leaf-table" v-if="suiteLeaves && suiteLeaves.length > 0">
                        <thead>
                            <tr>
                                <th style="width: 32px;">
                                    <input type="checkbox"
                                           class="leaf-checkbox"
                                           :checked="allChecked"
                                           :indeterminate.prop="someChecked"
                                           @change="toggleAll"
                                           :disabled="running">
                                </th>
                                <th>Name</th>
                                <th style="width: 70px; text-align: center;">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="leaf in suiteLeaves" :key="leaf.name"
                                :class="{ 'leaf-row-checked': selectedLeaves[leaf.name] }"
                                @click="$emit('selectLeaf', { suite: suiteData, leaf })"
                                style="cursor: pointer;">
                                <td @click.stop>
                                    <input type="checkbox"
                                           class="leaf-checkbox"
                                           :checked="selectedLeaves[leaf.name]"
                                           @change="toggleLeaf(leaf.name)"
                                           :disabled="running">
                                </td>
                                <td>{{ leaf.name }}</td>
                                <td style="text-align: center;" :class="statusClass(leaf.name)">
                                    {{ statusIcon(leaf.name) }}
                                </td>
                            </tr>
                        </tbody>
                    </table>

                    <div v-else-if="suiteLeaves && suiteLeaves.length === 0" style="color: var(--text-secondary); padding: 2rem; text-align: center;">
                        <p>No subfolders found at this path.</p>
                        <p style="font-size: 0.8rem; margin-top: 0.5rem;">Check the folder path in <a href="#" @click.prevent="viewMode = 'config'" style="color: var(--accent);">Config</a>.</p>
                    </div>

                    <div v-else style="color: var(--text-secondary); padding: 2rem; text-align: center;">
                        <span class="spinner"></span> Loading leaves...
                    </div>
                </template>
            </template>

            <!-- Leaf selected: show result -->
            <template v-else-if="selectedNode.type === 'leaf'">
                <div class="content-header">
                    <h2>{{ selectedNode.leaf.name }}</h2>
                    <button class="btn btn-secondary" @click="$emit('selectLeaf', null)">Back to List</button>
                </div>
                <div v-if="running" style="margin-bottom: 1rem;">
                    <span class="spinner"></span> Running...
                </div>
                <div v-if="leafResult && leafResult.status === 'error'" style="background: rgba(239,68,68,0.1); padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">
                    <strong class="status-error">Error:</strong> {{ leafResult.error_message }}
                </div>
                <div v-if="leafResult && leafResult.status === 'timeout'" style="background: rgba(245,158,11,0.1); padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">
                    <strong class="status-timeout">Timeout:</strong> {{ leafResult.error_message }}
                </div>
                <div v-if="renderData">
                    <table-renderer v-if="effectiveType === 'table'" :data="renderData"></table-renderer>
                    <diff-renderer v-else-if="effectiveType === 'diff'" :data="renderData"></diff-renderer>
                    <html-renderer v-else-if="effectiveType === 'html'" :data="renderData"></html-renderer>
                    <sections-renderer v-else-if="effectiveType === 'sections'" :data="renderData"></sections-renderer>
                    <pre v-else style="color: var(--text-secondary);">{{ JSON.stringify(renderData, null, 2) }}</pre>
                </div>
                <div v-else-if="!running && !leafResult" style="color: var(--text-secondary);">
                    No results yet. Run the suite or right-click this item to run individually.
                </div>
            </template>
        </div>
    `,
};
