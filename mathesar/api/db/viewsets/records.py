from psycopg2.errors import NotNullViolation

from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.renderers import BrowsableAPIRenderer
from sqlalchemy.exc import IntegrityError
from sqlalchemy_filters.exceptions import BadSortFormat, SortFieldNotFound

from db.functions.exceptions import BadDBFunctionFormat, UnknownDBFunctionId, ReferencedColumnsDontExist
from db.records.exceptions import BadGroupFormat, GroupFieldNotFound, InvalidGroupType

import mathesar.api.exceptions.database_exceptions.exceptions as database_api_exceptions
from mathesar.api.pagination import TableLimitOffsetGroupPagination
from mathesar.api.serializers.records import RecordListParameterSerializer, RecordSerializer
from mathesar.api.utils import get_table_or_404
from mathesar.models import Table
from mathesar.utils.json import MathesarJSONRenderer


class RecordViewSet(viewsets.ViewSet):
    # There is no 'update' method.
    # We're not supporting PUT requests because there aren't a lot of use cases
    # where the entire record needs to be replaced, PATCH suffices for updates.
    def get_queryset(self):
        return Table.objects.all().order_by('-created_at')

    renderer_classes = [MathesarJSONRenderer, BrowsableAPIRenderer]

    # For filter parameter formatting, see:
    # db/functions/operations/deserialize.py::get_db_function_from_ma_function_spec function doc>
    # For sorting parameter formatting, see:
    # https://github.com/centerofci/sqlalchemy-filters#sort-format
    def list(self, request, table_pk=None):
        paginator = TableLimitOffsetGroupPagination()

        serializer = RecordListParameterSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        try:
            records = paginator.paginate_queryset(
                self.get_queryset(), request, table_pk,
                filter=serializer.validated_data['filter'],
                order_by=serializer.validated_data['order_by'],
                grouping=serializer.validated_data['grouping'],
                duplicate_only=serializer.validated_data['duplicate_only'],
            )
        except (BadDBFunctionFormat, UnknownDBFunctionId, ReferencedColumnsDontExist) as e:
            raise database_api_exceptions.BadFilterAPIException(
                e,
                field='filters',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except (BadSortFormat, SortFieldNotFound) as e:
            raise database_api_exceptions.BadSortAPIException(
                e,
                field='order_by',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except (BadGroupFormat, GroupFieldNotFound, InvalidGroupType) as e:
            raise database_api_exceptions.BadGroupAPIException(
                e,
                field='grouping',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        serializer = RecordSerializer(records, many=True)
        return paginator.get_paginated_response(serializer.data)

    def retrieve(self, request, pk=None, table_pk=None):
        table = get_table_or_404(table_pk)
        record = table.get_record(pk)
        if not record:
            raise NotFound
        serializer = RecordSerializer(record)
        return Response(serializer.data)

    def create(self, request, table_pk=None):
        table = get_table_or_404(table_pk)
        # We only support adding a single record through the API.
        assert isinstance((request.data), dict)
        try:
            record = table.create_record_or_records(request.data)
        except IntegrityError as e:
            if type(e.orig) == NotNullViolation:
                raise database_api_exceptions.NotNullViolationAPIException(
                    e,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    table=table
                )
            else:
                raise database_api_exceptions.MathesarAPIException(e, status_code=status.HTTP_400_BAD_REQUEST)
        serializer = RecordSerializer(record)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None, table_pk=None):
        table = get_table_or_404(table_pk)
        record = table.update_record(pk, request.data)
        serializer = RecordSerializer(record)
        return Response(serializer.data)

    def destroy(self, request, pk=None, table_pk=None):
        table = get_table_or_404(table_pk)
        table.delete_record(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)