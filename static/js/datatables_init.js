/* SPORTS-MAX — Inicializador común de DataTables (paginación, orden y búsqueda en español) */
(function () {
    'use strict';

    var ES = {
        decimal: ',',
        thousands: '.',
        emptyTable: 'No hay datos disponibles en la tabla',
        info: 'Mostrando _START_ a _END_ de _TOTAL_ registros',
        infoEmpty: 'Mostrando 0 a 0 de 0 registros',
        infoFiltered: '(filtrado de _MAX_ registros en total)',
        lengthMenu: 'Mostrar _MENU_ registros',
        loadingRecords: 'Cargando...',
        processing: 'Procesando...',
        search: 'Buscar:',
        searchPlaceholder: 'Escribe para buscar...',
        zeroRecords: 'No se encontraron resultados',
        paginate: { first: '«', last: '»', next: 'Siguiente', previous: 'Anterior' },
        aria: {
            orderable: 'Activar para ordenar la columna',
            orderableReverse: 'Activar para ordenar en forma descendente',
            orderableRemove: 'Activar para quitar el orden',
            paginate: { first: 'Primera página', last: 'Última página', next: 'Página siguiente', previous: 'Página anterior' }
        }
    };

    window.smaxDataTable = function (selector, options) {
        var el = document.querySelector(selector);
        if (!el || typeof DataTable === 'undefined') return null;
        var defaults = {
            language: ES,
            pageLength: 10,
            lengthMenu: [5, 10, 25, 50, 100],
            order: [],
            autoWidth: false,
            columnDefs: [{ targets: 'no-orden', orderable: false, searchable: false }],
            layout: {
                topStart: 'pageLength',
                topEnd: 'search',
                bottomStart: 'info',
                bottomEnd: 'paging'
            }
        };
        return new DataTable(el, Object.assign(defaults, options || {}));
    };
})();

