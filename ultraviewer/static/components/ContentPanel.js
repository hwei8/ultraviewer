const ContentPanel = {
    props: ['selectedNode', 'suiteData', 'leafResult', 'running', 'progress'],
    emits: ['saveSettings', 'runSuite', 'testScript'],
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
    },
    template: `
        <div class="content-panel">
            <!-- Nothing selected -->
            <div v-if="!selectedNode" style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-secondary);">
                Select a suite or folder from the tree
            </div>

            <!-- Suite selected: show settings -->
            <template v-else-if="selectedNode.type === 'suite' && suiteData">
                <div class="content-header">
                    <h2>{{ suiteData.name }} - Settings</h2>
                    <button class="btn btn-primary" @click="$emit('runSuite', suiteData)">Run Suite</button>
                </div>
                <suite-settings
                    :suite="suiteData"
                    @save="$emit('saveSettings', $event)"
                    @test-script="$emit('testScript', $event)"
                ></suite-settings>
            </template>

            <!-- Leaf selected: show result -->
            <template v-else-if="selectedNode.type === 'leaf'">
                <div class="content-header">
                    <h2>{{ selectedNode.leaf.name }}</h2>
                </div>
                <div v-if="running" style="margin-bottom: 1rem;">
                    <span class="spinner"></span> Running...
                    <div class="progress-bar" v-if="progress">
                        <div class="progress-fill" :style="{ width: (progress.done / progress.total * 100) + '%' }"></div>
                    </div>
                </div>
                <div v-if="leafResult && leafResult.status === 'error'" style="background: rgba(239,68,68,0.1); padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">
                    <strong class="status-error">Error:</strong> {{ leafResult.error_message }}
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
