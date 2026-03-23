const DiffRenderer = {
    props: ['data'],
    computed: {
        files() {
            return this.data?.files || [];
        },
    },
    methods: {
        diffLines(golden, actual) {
            const gLines = (golden || '').split('\n');
            const aLines = (actual || '').split('\n');
            const maxLen = Math.max(gLines.length, aLines.length);
            const result = [];
            for (let i = 0; i < maxLen; i++) {
                const g = gLines[i] || '';
                const a = aLines[i] || '';
                if (g === a) {
                    result.push({ type: 'same', line: g, num: i + 1 });
                } else {
                    if (g) result.push({ type: 'remove', line: g, num: i + 1 });
                    if (a) result.push({ type: 'add', line: a, num: i + 1 });
                }
            }
            return result;
        },
    },
    template: `
        <div class="diff-container" v-for="file in files" :key="file.name" style="margin-bottom: 1rem;">
            <div class="diff-file-header">{{ file.name }}</div>
            <div class="diff-content"><template v-for="line in diffLines(file.golden, file.actual)"
><span :class="{ 'diff-add': line.type === 'add', 'diff-remove': line.type === 'remove' }"
>{{ line.type === 'remove' ? '-' : line.type === 'add' ? '+' : ' ' }} {{ line.line }}
</span></template></div>
        </div>
        <p v-if="files.length === 0" style="color: var(--text-secondary); padding: 1rem;">No diffs</p>
    `,
};
