const HtmlRenderer = {
    props: ['data'],
    computed: {
        htmlContent() {
            return this.data?.content || '';
        },
    },
    template: `
        <div class="html-renderer" v-html="htmlContent"></div>
    `,
};
