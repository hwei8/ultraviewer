const TreeView = {
    props: ['suites', 'selectedNode'],
    emits: ['selectSuite', 'selectLeaf', 'createSuite', 'runSuite', 'runLeaf', 'deleteSuite'],
    data() {
        return {
            expandedSuites: {},
            suiteLeaves: {},
            loadingLeaves: {},
            contextMenu: null,
        };
    },
    methods: {
        async toggleSuite(suite) {
            const id = suite.id;
            if (this.expandedSuites[id]) {
                this.expandedSuites[id] = false;
            } else {
                this.expandedSuites[id] = true;
                if (!this.suiteLeaves[id]) {
                    await this.loadLeaves(suite);
                }
            }
        },
        async loadLeaves(suite) {
            this.loadingLeaves[suite.id] = true;
            try {
                const resp = await fetch(`/api/suites/${suite.id}/leaves`);
                const leaves = await resp.json();
                this.suiteLeaves[suite.id] = leaves;
            } catch (e) {
                this.suiteLeaves[suite.id] = [];
            }
            this.loadingLeaves[suite.id] = false;
        },
        onSuiteContextMenu(e, suite) {
            e.preventDefault();
            e.stopPropagation();
            this.contextMenu = { x: e.clientX, y: e.clientY, type: 'suite', item: suite };
        },
        onLeafContextMenu(e, suite, leaf) {
            e.preventDefault();
            e.stopPropagation();
            this.contextMenu = { x: e.clientX, y: e.clientY, type: 'leaf', item: leaf, suite };
        },
        closeContextMenu() {
            this.contextMenu = null;
        },
        isSelected(type, id) {
            return this.selectedNode && this.selectedNode.type === type && this.selectedNode.id === id;
        },
        async refreshLeaves(suiteId) {
            const suite = this.suites.find(s => s.id === suiteId);
            if (suite) await this.loadLeaves(suite);
        },
        confirmDeleteSuite(suite) {
            this.contextMenu = null;
            if (confirm(`Delete suite "${suite.name}"? This will also remove all its run results.`)) {
                this.$emit('deleteSuite', suite);
            }
        },
    },
    mounted() {
        document.addEventListener('click', this.closeContextMenu);
    },
    unmounted() {
        document.removeEventListener('click', this.closeContextMenu);
    },
    template: `
        <div class="tree-panel">
            <div class="tree-header">
                <h3>Explorer</h3>
                <button class="tree-add-btn" @click="$emit('createSuite')">+ Suite</button>
            </div>
            <div class="tree-body">
                <div v-for="suite in suites" :key="suite.id">
                    <div class="tree-node"
                         :class="{ selected: isSelected('suite', suite.id) }"
                         @click="$emit('selectSuite', suite); toggleSuite(suite)"
                         @contextmenu="onSuiteContextMenu($event, suite)">
                        <span class="icon">{{ expandedSuites[suite.id] ? '\u25BC' : '\u25B6' }}</span>
                        {{ suite.name }}
                    </div>
                    <template v-if="expandedSuites[suite.id]">
                        <div v-if="loadingLeaves[suite.id]" class="tree-node tree-leaf">
                            <span class="spinner"></span> Loading...
                        </div>
                        <div v-else-if="suiteLeaves[suite.id]?.length === 0" class="tree-node tree-leaf" style="color: var(--text-secondary);">
                            (empty)
                        </div>
                        <div v-else v-for="leaf in suiteLeaves[suite.id]" :key="leaf.path"
                             class="tree-node tree-leaf"
                             :class="{ selected: isSelected('leaf', leaf.path) }"
                             @click.stop="$emit('selectLeaf', { suite, leaf })"
                             @contextmenu="onLeafContextMenu($event, suite, leaf)">
                            {{ leaf.name }}
                        </div>
                    </template>
                </div>
                <div v-if="suites.length === 0" style="padding: 1rem; color: var(--text-secondary); font-size: 0.82rem;">
                    No suites yet. Click "+ Suite" to add one.
                </div>
            </div>

            <Teleport to="body">
                <div v-if="contextMenu" class="context-menu"
                     :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
                     @click.stop>
                    <template v-if="contextMenu.type === 'suite'">
                        <div class="context-menu-item" @click="$emit('runSuite', contextMenu.item); closeContextMenu()">Run Suite</div>
                        <div class="context-menu-item" @click="refreshLeaves(contextMenu.item.id); closeContextMenu()">Rescan</div>
                        <div class="context-menu-item danger" @click.stop="confirmDeleteSuite(contextMenu.item)">Delete Suite</div>
                    </template>
                    <template v-if="contextMenu.type === 'leaf'">
                        <div class="context-menu-item" @click="$emit('runLeaf', { suite: contextMenu.suite, leaf: contextMenu.item }); closeContextMenu()">Run This</div>
                    </template>
                </div>
            </Teleport>
        </div>
    `,
};
