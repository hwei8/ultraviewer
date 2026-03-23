const TabBar = {
    props: ['tabs', 'activeTabId'],
    emits: ['select', 'create', 'rename', 'delete'],
    data() {
        return {
            contextMenu: null,
            editingTabId: null,
            editName: '',
        };
    },
    methods: {
        onContextMenu(e, tab) {
            e.preventDefault();
            this.contextMenu = { x: e.clientX, y: e.clientY, tab };
        },
        closeContextMenu() {
            this.contextMenu = null;
        },
        startRename(tab) {
            this.editingTabId = tab.id;
            this.editName = tab.name;
            this.closeContextMenu();
            this.$nextTick(() => {
                const input = this.$el.querySelector('.tab-edit-input');
                if (input) input.focus();
            });
        },
        finishRename() {
            if (this.editName.trim() && this.editingTabId) {
                this.$emit('rename', { id: this.editingTabId, name: this.editName.trim() });
            }
            this.editingTabId = null;
        },
        cancelRename() {
            this.editingTabId = null;
        },
    },
    mounted() {
        document.addEventListener('click', this.closeContextMenu);
    },
    unmounted() {
        document.removeEventListener('click', this.closeContextMenu);
    },
    template: `
        <div class="tab-bar">
            <div v-for="tab in tabs" :key="tab.id"
                 class="tab-item"
                 :class="{ active: tab.id === activeTabId }"
                 @click="$emit('select', tab.id)"
                 @contextmenu="onContextMenu($event, tab)"
                 @dblclick="startRename(tab)">
                <template v-if="editingTabId === tab.id">
                    <input class="tab-edit-input"
                           v-model="editName"
                           @keydown.enter="finishRename"
                           @keydown.escape="cancelRename"
                           @blur="finishRename"
                           @click.stop
                           style="background:transparent;border:none;color:#fff;width:80px;outline:none;">
                </template>
                <template v-else>{{ tab.name }}</template>
            </div>
            <div class="tab-add" @click="$emit('create')">+</div>

            <div v-if="contextMenu" class="context-menu"
                 :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }">
                <div class="context-menu-item" @click="startRename(contextMenu.tab)">Rename</div>
                <div class="context-menu-item danger" @click="$emit('delete', contextMenu.tab.id); closeContextMenu()">Delete</div>
            </div>
        </div>
    `,
};
