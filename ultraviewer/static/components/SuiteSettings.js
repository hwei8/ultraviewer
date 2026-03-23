const SuiteSettings = {
    props: ['suite'],
    emits: ['save', 'testScript'],
    data() {
        return {
            form: this.initForm(),
        };
    },
    watch: {
        suite: {
            handler() { this.form = this.initForm(); },
            deep: true,
        },
    },
    methods: {
        initForm() {
            const s = this.suite || {};
            const script = s.script || {};
            const rendering = s.rendering || {};
            return {
                name: s.name || '',
                folder_path: s.folder_path || '',
                scan_depth: s.scan_depth || 1,
                interpreter: script.interpreter || 'python3',
                script_path: script.script_path || '',
                timeout_seconds: script.timeout_seconds || 30,
                max_parallel: script.max_parallel || 1,
                extra_args: (script.extra_args || []).map(a => ({...a})),
                env_vars: (script.env_vars || []).map(v => ({...v})),
                render_mode: rendering.render_mode || 'auto',
                render_config: rendering.config || {},
            };
        },
        addArg() { this.form.extra_args.push({ key: '', value: '' }); },
        removeArg(i) { this.form.extra_args.splice(i, 1); },
        addEnv() { this.form.env_vars.push({ key: '', value: '' }); },
        removeEnv(i) { this.form.env_vars.splice(i, 1); },
        save() {
            this.$emit('save', {
                id: this.suite.id,
                name: this.form.name,
                folder_path: this.form.folder_path,
                scan_depth: this.form.scan_depth,
                script: {
                    interpreter: this.form.interpreter,
                    script_path: this.form.script_path,
                    timeout_seconds: this.form.timeout_seconds,
                    extra_args: this.form.extra_args.filter(a => a.key),
                    env_vars: this.form.env_vars.filter(v => v.key),
                    max_parallel: this.form.max_parallel,
                },
                rendering: {
                    render_mode: this.form.render_mode,
                    config: this.form.render_config,
                },
            });
        },
    },
    template: `
        <div>
            <div class="settings-section">
                <h3>Basic</h3>
                <div class="form-row">
                    <label>Suite Name</label>
                    <input class="form-input" v-model="form.name">
                </div>
                <div class="form-row">
                    <label>Folder Path</label>
                    <folder-browser v-model="form.folder_path" mode="dir"></folder-browser>
                </div>
                <div class="form-row">
                    <label>Scan Depth</label>
                    <select class="form-select" v-model.number="form.scan_depth">
                        <option :value="1">1 level</option>
                        <option :value="2">2 levels</option>
                        <option :value="3">3 levels</option>
                    </select>
                </div>
            </div>

            <div class="settings-section">
                <h3>Script</h3>
                <div class="form-row">
                    <label>Interpreter</label>
                    <select class="form-select" v-model="form.interpreter">
                        <option value="python3">python3</option>
                        <option value="bash">bash</option>
                    </select>
                </div>
                <div class="form-row">
                    <label>Script Path</label>
                    <folder-browser v-model="form.script_path" mode="file"></folder-browser>
                </div>
                <div class="form-row">
                    <label>Timeout (sec)</label>
                    <input class="form-input" type="number" v-model.number="form.timeout_seconds" style="width: 100px;">
                </div>
                <div class="form-row">
                    <label>Max Parallel</label>
                    <input class="form-input" type="number" v-model.number="form.max_parallel" style="width: 100px;" min="1">
                </div>
            </div>

            <div class="settings-section">
                <h3>Context</h3>
                <p style="color: var(--text-secondary); font-size: 0.78rem; margin-bottom: 0.8rem;">
                    Leaf folder path is always passed as the first argument.
                </p>
                <div style="margin-bottom: 0.8rem;">
                    <label style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.3rem; display: block;">Extra Arguments</label>
                    <div class="kv-row" v-for="(arg, i) in form.extra_args" :key="i">
                        <input class="form-input" v-model="arg.key" placeholder="--flag">
                        <input class="form-input" v-model="arg.value" placeholder="value">
                        <button class="kv-remove" @click="removeArg(i)">x</button>
                    </div>
                    <button class="btn btn-sm btn-secondary" @click="addArg">+ Add Argument</button>
                </div>
                <div>
                    <label style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.3rem; display: block;">Environment Variables</label>
                    <div class="kv-row" v-for="(v, i) in form.env_vars" :key="i">
                        <input class="form-input" v-model="v.key" placeholder="VAR_NAME">
                        <input class="form-input" v-model="v.value" placeholder="value">
                        <button class="kv-remove" @click="removeEnv(i)">x</button>
                    </div>
                    <button class="btn btn-sm btn-secondary" @click="addEnv">+ Add Variable</button>
                </div>
            </div>

            <div class="settings-section">
                <h3>Rendering</h3>
                <div class="form-row">
                    <label>Render Mode</label>
                    <select class="form-select" v-model="form.render_mode">
                        <option value="auto">Auto (by type field)</option>
                        <option value="table">Table</option>
                        <option value="diff">Diff View</option>
                        <option value="html">Raw HTML</option>
                    </select>
                </div>
            </div>

            <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
                <button class="btn btn-secondary" @click="$emit('testScript', suite.id)">Test Script</button>
                <button class="btn btn-primary" @click="save">Save</button>
            </div>
        </div>
    `,
};
