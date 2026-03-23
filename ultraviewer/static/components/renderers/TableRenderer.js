const TableRenderer = {
    props: ['data'],
    computed: {
        columns() {
            return this.data?.columns || (this.data?.rows?.length ? Object.keys(this.data.rows[0]) : []);
        },
        rows() {
            return this.data?.rows || [];
        },
    },
    template: `
        <table class="data-table">
            <thead>
                <tr>
                    <th v-for="col in columns" :key="col">{{ col }}</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="(row, i) in rows" :key="i">
                    <td v-for="col in columns" :key="col"
                        :class="{
                            'status-pass': row[col] === 'pass' || row[col] === 'PASS',
                            'status-fail': row[col] === 'fail' || row[col] === 'FAIL',
                            'status-error': row[col] === 'error' || row[col] === 'ERROR',
                        }">
                        {{ row[col] }}
                    </td>
                </tr>
            </tbody>
        </table>
        <p v-if="rows.length === 0" style="color: var(--text-secondary); padding: 1rem;">No data</p>
    `,
};
