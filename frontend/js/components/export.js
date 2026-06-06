/* Utility for Exporting Data */
const DataExport = (() => {
    function exportToCSV(filename, headers, dataRows) {
        if (!dataRows || !dataRows.length) {
            if(window.Toast) Toast.info("No data to export");
            return;
        }
        
        const rows = [headers, ...dataRows];
        
        const processRow = function(row) {
            let finalVal = '';
            for (let j = 0; j < row.length; j++) {
                let innerValue = row[j] === null || row[j] === undefined ? '' : row[j].toString();
                if (row[j] instanceof Date) {
                    innerValue = row[j].toLocaleString();
                }
                // Strip HTML tags
                innerValue = innerValue.replace(/<[^>]+>/g, '').trim();
                
                let result = innerValue.replace(/"/g, '""');
                if (result.search(/("|,|\n)/g) >= 0)
                    result = '"' + result + '"';
                if (j > 0)
                    finalVal += ',';
                finalVal += result;
            }
            return finalVal + '\n';
        };

        let csvFile = '';
        for (let i = 0; i < rows.length; i++) {
            csvFile += processRow(rows[i]);
        }

        const blob = new Blob([csvFile], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute("href", url);
            link.setAttribute("download", filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }

    return { exportToCSV };
})();
