const FolderBrowser = {
    props: {
        modelValue: { type: String, default: '' },
        mode: { type: String, default: 'dir' }, // 'dir' or 'file'
        label: { type: String, default: 'Path' },
    },
    emits: ['update:modelValue'],
    data() {
        return {
            showBrowser: false,
            currentPath: '',
            entries: [],
            parentPath: '',
            loading: false,
            error: null,
        };
    },
    methods: {
        async openBrowser() {
            this.showBrowser = true;
            const startPath = this.modelValue || '~';
            // If modelValue is a file path, start from its directory
            if (this.mode === 'file' && this.modelValue) {
                const parts = this.modelValue.split('/');
                parts.pop();
                await this.browse(parts.join('/') || '/');
            } else {
                await this.browse(startPath);
            }
        },
        async browse(path) {
            this.loading = true;
            this.error = null;
            try {
                const resp = await fetch(`/api/browse?path=${encodeURIComponent(path)}`);
                const data = await resp.json();
                this.currentPath = data.path;
                this.parentPath = data.parent;
                this.entries = data.entries || [];
                if (data.error) this.error = data.error;
            } catch (e) {
                this.error = 'Failed to browse';
            }
            this.loading = false;
        },
        navigateUp() {
            if (this.parentPath && this.parentPath !== this.currentPath) {
                this.browse(this.parentPath);
            }
        },
        onEntryClick(entry) {
            if (entry.type === 'dir') {
                this.browse(entry.path);
            } else if (this.mode === 'file') {
                this.selectPath(entry.path);
            }
        },
        selectPath(path) {
            this.$emit('update:modelValue', path || this.currentPath);
            this.showBrowser = false;
        },
        selectCurrent() {
            this.selectPath(this.currentPath);
        },
    },
    template: `
        <div>
            <div style="display: flex; gap: 0.5rem; align-items: center;">
                <input class="form-input" :value="modelValue"
                       @input="$emit('update:modelValue', $event.target.value)"
                       :placeholder="mode === 'file' ? '/path/to/script.py' : '/path/to/folder'">
                <button class="btn btn-sm btn-secondary" @click="openBrowser"
                        style="white-space: nowrap; flex-shrink: 0;">Browse</button>
            </div>

            <div v-if="showBrowser" class="modal-overlay" @click.self="showBrowser = false">
                <div class="modal" style="min-width: 550px; max-width: 650px; max-height: 80vh; display: flex; flex-direction: column;">
                    <h3 style="margin-bottom: 0.5rem;">{{ mode === 'file' ? 'Select File' : 'Select Folder' }}</h3>

                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                        <button class="btn btn-sm btn-secondary" @click="navigateUp"
                                :disabled="!parentPath || parentPath === currentPath">^</button>
                        <input class="form-input" v-model="currentPath"
                               @keydown.enter="browse(currentPath)"
                               style="font-size: 0.78rem; font-family: monospace;">
                        <button class="btn btn-sm btn-secondary" @click="browse(currentPath)">Go</button>
                    </div>

                    <div v-if="error" style="color: var(--error); font-size: 0.8rem; margin-bottom: 0.5rem;">{{ error }}</div>

                    <div style="flex: 1; overflow-y: auto; border: 1px solid var(--border); border-radius: 4px; max-height: 400px;">
                        <div v-if="loading" style="padding: 1rem; color: var(--text-secondary); text-align: center;">
                            <span class="spinner"></span> Loading...
                        </div>
                        <template v-else>
                            <div v-for="entry in entries" :key="entry.path"
                                 class="browser-entry"
                                 :class="{ 'browser-dir': entry.type === 'dir' }"
                                 @click="onEntryClick(entry)"
                                 @dblclick="entry.type === 'dir' && mode === 'dir' ? selectPath(entry.path) : null">
                                <span style="margin-right: 0.4rem; opacity: 0.7;">{{ entry.type === 'dir' ? '&#x1F4C1;' : '&#x1F4C4;' }}</span>
                                {{ entry.name }}
                            </div>
                            <div v-if="entries.length === 0" style="padding: 1rem; color: var(--text-secondary); text-align: center; font-size: 0.82rem;">
                                Empty directory
                            </div>
                        </template>
                    </div>

                    <div class="modal-actions" style="margin-top: 0.8rem;">
                        <button class="btn btn-secondary" @click="showBrowser = false">Cancel</button>
                        <button v-if="mode === 'dir'" class="btn btn-primary" @click="selectCurrent">
                            Select This Folder
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `,
};
