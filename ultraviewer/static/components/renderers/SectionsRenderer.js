const SectionsRenderer = {
    props: ['data'],
    computed: {
        sections() {
            return this.data?.sections || [];
        },
    },
    template: `
        <div v-for="(section, i) in sections" :key="i" style="margin-bottom: 1.5rem;">
            <table-renderer v-if="section.type === 'table'" :data="section"></table-renderer>
            <diff-renderer v-else-if="section.type === 'diff'" :data="section"></diff-renderer>
            <html-renderer v-else-if="section.type === 'html'" :data="section"></html-renderer>
            <div v-else style="color: var(--text-secondary);">Unknown section type: {{ section.type }}</div>
        </div>
    `,
};
