import argparse
import configparser
import flask
import requests
import sys
import sqlalchemy
import pandas
from requests.utils import dict_to_sequence

from sqlalchemy.orm import sessionmaker

from . import create_app
from . import database
from . import models

class Process:
    @classmethod
    def biomarkers(cls, biomarker_records):
        biomarker_to_proposition_count = cls.get_counts(
            ids=biomarker_records.get('id').unique(),
            dataframe=biomarker_records,
            id_column='id',
            count_column='proposition_id'
        )
        biomarker_to_statement_count = cls.get_counts(
            ids=biomarker_records.get('id').unique(),
            dataframe=biomarker_records,
            id_column='id',
            count_column='statement_id'
        )
        biomarker_records['propositions_count'] = biomarker_records.get('id').replace(biomarker_to_proposition_count)
        biomarker_records['statements_count'] = biomarker_records.get('id').replace(biomarker_to_statement_count)
        return (
            biomarker_records
            .drop(['proposition_id', 'statement_id'], axis='columns')
            .drop_duplicates()
        )

    @classmethod
    def diseases(cls, disease_records):
        disease_to_proposition_count = cls.get_counts(
            ids=disease_records.get('id').unique(),
            dataframe=disease_records,
            id_column='id',
            count_column='proposition_id'
        )
        disease_to_statement_count = cls.get_counts(
            ids=disease_records.get('id').unique(),
            dataframe=disease_records,
            id_column='id',
            count_column='statement_id'
        )
        disease_records['propositions_count'] = disease_records.get('id').replace(disease_to_proposition_count)
        disease_records['statements_count'] = disease_records.get('id').replace(disease_to_statement_count)
        return (
            disease_records
            .drop(['proposition_id', 'statement_id'], axis='columns')
            .drop_duplicates()
        )

    @classmethod
    def documents(cls, document_records, indication_records):
        document_to_statement_count = cls.get_counts(
            ids=document_records.get('id').unique(),
            dataframe=document_records,
            id_column='id',
            count_column='statement_id'
        )
        document_to_indication_count = cls.get_counts(
            ids=document_records.get('id').unique(),
            dataframe=indication_records,
            id_column='document_id',
            count_column='id'
        )
        document_records['indications_count'] = document_records.get('id').replace(document_to_indication_count)
        document_records['statements_count'] = document_records.get('id').replace(document_to_statement_count)
        return (
            document_records
            .drop('statement_id', axis='columns')
            .drop_duplicates()
        )

    @classmethod
    def genes(cls, gene_records):
        gene_to_biomarker_count = cls.get_counts(
            ids=gene_records.get('id').unique(),
            dataframe=gene_records,
            id_column='id',
            count_column='biomarker_id'
        )
        gene_to_proposition_count = cls.get_counts(
            ids=gene_records.get('id').unique(),
            dataframe=gene_records,
            id_column='id',
            count_column='proposition_id'
        )
        gene_to_statement_count = cls.get_counts(
            ids=gene_records.get('id').unique(),
            dataframe=gene_records,
            id_column='id',
            count_column='statement_id'
        )
        gene_records['biomarkers_count'] = gene_records.get('id').replace(gene_to_biomarker_count)
        gene_records['propositions_count'] = gene_records.get('id').replace(gene_to_proposition_count)
        gene_records['statements_count'] = gene_records.get('id').replace(gene_to_statement_count)
        return (
            gene_records
            .drop(['biomarker_id', 'proposition_id', 'statement_id'], axis='columns')
            .drop_duplicates()
        )

    @classmethod
    def get_biomarker(cls, record, proposition_id, statement_id):
        extensions = record.get('extensions')
        biomarker_type = cls.get_value_by_name(data=extensions, name='biomarker_type')
        return {
            'id': record.get('id'),
            'name': record.get('name'),
            'type': biomarker_type,
            'proposition_id': proposition_id,
            'statement_id': statement_id
        }

    @staticmethod
    def get_counts(ids, dataframe, id_column, count_column):
        dictionary = {}
        for item_id in ids:
            counts = dataframe.loc[dataframe[id_column].eq(item_id), count_column].drop_duplicates().shape[0]
            dictionary[item_id] = counts
        return dictionary

    @classmethod
    def get_disease(cls, record, proposition_id, statement_id):
        return {
            'id': record.get('id'),
            'name': record.get('name'),
            'proposition_id': proposition_id,
            'statement_id': statement_id
        }

    @classmethod
    def get_document(cls, record, statement_id):
        return {
            'id': record.get('id'),
            'name': record.get('name'),
            'citation': record.get('citation'),
            'url': record.get('url'),
            'organization_id': record.get('organization').get('id'),
            'organization_name': record.get('organization').get('name'),
            'statement_id': statement_id
        }

    @staticmethod
    def get_value_by_name(data, name):
        """
        Retrieve the 'value' corresponding to the given 'name' from a list of dictionaries.

        Parameters:
            data (list of dict): List containing dictionaries with 'name' and 'value' keys.
            name (str): The name to search for.

        Returns:
            The value associated with the given name.

        Raises:
            ValueError: If the name is not found in the list.
        """
        for item in data:
            if item.get("name") == name:
                return item.get("value")
        raise ValueError(f"Name '{name}' not found in data.")

    @classmethod
    def get_gene(cls, record, biomarker_id, proposition_id, statement_id):
        return {
            'id': record.get('id'),
            'name': record.get('name'),
            'biomarker_id': biomarker_id,
            'proposition_id': proposition_id,
            'statement_id': statement_id
        }

    @classmethod
    def get_indication(cls, record, statement_id):
        return {
            'id': record.get('id'),
            'indication': record.get('indication'),
            'document_id': record.get('document').get('id'),
            'organization_id': record.get('document').get('organization').get('id'),
            'organization_name': record.get('document').get('organization').get('name'),
            'statement_id': statement_id
        }

    @classmethod
    def get_therapeutic(cls, record, proposition_id, statement_id):
        if 'therapies' in record:
            therapies = []
            for therapy in record.get('therapies'):
                therapy_type = [ext.get('value') for ext in therapy.get('extensions') if ext.get('name') == 'therapy_type'][0]
                therapies.append({
                    'id': therapy.get('id'),
                    'name': therapy.get('name'),
                    # therapy strategy
                    'therapy_type': therapy_type,
                    'proposition_id': proposition_id,
                    'statement_id': statement_id
                })
            return therapies
        else:
            therapy = record
            therapy_type = [ext.get('value') for ext in therapy.get('extensions') if ext.get('name') == 'therapy_type'][0]
            return [{
                'id': therapy.get('id'),
                'name': therapy.get('name'),
                # therapy _strategy
                'therapy_type': therapy_type,
                'proposition_id': proposition_id,
                'statement_id': statement_id
            }]

    @classmethod
    def indications(cls, indication_records):
        indication_to_statement_count = cls.get_counts(
            ids=indication_records.get('id').unique(),
            dataframe=indication_records,
            id_column='id',
            count_column='statement_id'
        )
        indication_records['statements_count'] = indication_records.get('id').replace(indication_to_statement_count)
        return (
            indication_records
            .drop('statement_id', axis='columns')
            .drop_duplicates()
        )

    @classmethod
    def organizations(cls, document_records, indication_records):
        counts_by_documents = document_records.groupby(['organization_name'])['statements_count'].sum()
        counts_by_indications = indication_records.groupby(['organization_name'])['statements_count'].sum()
        for organization in counts_by_documents.index:
            if counts_by_documents[organization] != counts_by_indications[organization]:
                raise ValueError(f"Statements counts for {organization} do not match between documents and indications")

        counts_by_organization = (
                document_records
                .loc[:, ['organization_id', 'organization_name']]
                .rename(columns={'organization_id': 'id', 'organization_name': 'name'})
                .drop_duplicates()
        )
        counts_by_organization['documents_count'] = counts_by_organization['name'].map(
            document_records
            .loc[:, ['organization_name', 'id']]
            .drop_duplicates()
            .loc[:, 'organization_name']
            .value_counts()
        )
        counts_by_organization['indications_count'] = counts_by_organization['name'].map(
            indication_records
            .loc[:, ['organization_name', 'id']]
            .drop_duplicates()
            .loc[:, 'organization_name']
            .value_counts()
        )
        counts_by_organization['statements_count'] = counts_by_organization['name'].map(counts_by_documents)
        return counts_by_organization

    @classmethod
    def propositions(cls, statements):
        return {statement.get('proposition').get('id') for statement in statements}

    @classmethod
    def statements(cls, records):
        biomarker_records = []
        disease_records = []
        document_records = []
        gene_records = []
        indication_records = []
        therapy_records = []
        for record in records:
            statement_id = record.get('id')
            for document in record.get('reportedIn'):
                record_document = cls.get_document(record=document, statement_id=statement_id)
                document_records.append(record_document)

            record_indication = cls.get_indication(record=record.get('indication'), statement_id=statement_id)
            indication_records.append(record_indication)

            proposition = record.get('proposition')
            for biomarker in proposition.get('biomarkers'):
                record_biomarker = cls.get_biomarker(
                    record=biomarker,
                    proposition_id=proposition.get('id'),
                    statement_id=statement_id
                )
                biomarker_records.append(record_biomarker)
                if 'genes' in biomarker:
                    for gene in biomarker.get('genes'):
                        record_gene = cls.get_gene(
                            record=gene,
                            biomarker_id=biomarker.get('id'),
                            proposition_id=proposition.get('id'),
                            statement_id=statement_id
                        )
                        gene_records.append(record_gene)

            record_disease = cls.get_disease(
                record=proposition.get('conditionQualifier'),
                proposition_id=proposition.get('id'),
                statement_id=statement_id
            )
            disease_records.append(record_disease)

            record_therapeutic = cls.get_therapeutic(
                record=proposition.get('objectTherapeutic'),
                proposition_id=proposition.get('id'),
                statement_id=statement_id
            )
            therapy_records.extend(record_therapeutic)

        biomarker_records = pandas.DataFrame(biomarker_records)
        disease_records = pandas.DataFrame(disease_records)
        document_records = pandas.DataFrame(document_records)
        gene_records = pandas.DataFrame(gene_records)
        indication_records = pandas.DataFrame(indication_records)
        therapy_records = pandas.DataFrame(therapy_records)

        biomarker_records = cls.biomarkers(biomarker_records=biomarker_records)
        disease_records = cls.diseases(disease_records=disease_records)
        document_records = cls.documents(document_records=document_records, indication_records=indication_records)
        gene_records =cls.genes(gene_records=gene_records)
        indication_records = cls.indications(indication_records=indication_records)
        organization_records = cls.organizations(
            document_records=document_records,
            indication_records=indication_records
        )
        therapy_records = cls.therapies(therapy_records=therapy_records)

        propositions = cls.propositions(statements=records)

        return {
            'biomarkers': biomarker_records.to_dict(orient='records'),
            'diseases': disease_records.to_dict(orient='records'),
            'documents': document_records.to_dict(orient='records'),
            'genes': gene_records.to_dict(orient='records'),
            'indications': indication_records.to_dict(orient='records'),
            'organizations': organization_records.to_dict(orient='records'),
            'therapies': therapy_records.to_dict(orient='records'),
            'propositions_count': propositions.__len__(),
            'statements_count': records.__len__(),
        }

    @classmethod
    def therapies(cls, therapy_records):
        therapy_to_proposition_count = cls.get_counts(
            ids=therapy_records.get('id').unique(),
            dataframe=therapy_records,
            id_column='id',
            count_column='proposition_id'
        )
        therapy_to_statement_count = cls.get_counts(
            ids=therapy_records.get('id').unique(),
            dataframe=therapy_records,
            id_column='id',
            count_column='statement_id'
        )
        therapy_records['propositions_count'] = therapy_records.get('id').astype(int).replace(therapy_to_proposition_count)
        therapy_records['statements_count'] = therapy_records.get('id').astype(int).replace(therapy_to_statement_count)
        return (
            therapy_records
            .drop(['proposition_id', 'statement_id'], axis='columns')
            .drop_duplicates()
        )

class Requests:
    @staticmethod
    def check_request(response, failure_message):
        if response.status_code not in [200, 201, 202, 204]:
            sys.exit(f"{failure_message}: {response.status_code}")
        else:
            return response

    @staticmethod
    def return_json(response):
        return response.json()

    @staticmethod
    def get_request(request):
        request = request.replace(' ', '%20')
        return requests.get(request)

    @classmethod
    def get_service(cls, root_url):
        request = f"{root_url}/about"
        response = cls.get_request(request=request)
        return cls.check_request(
            response=response,
            failure_message=f"Failed to get service information from moalmanac api at {root_url}"
        )

    @classmethod
    def get_statements(cls, root_url, filters=None):
        request = f"{root_url}/statements"
        if filters:
            request = f"{request}?{'&'.join(filters)}"
        response = cls.get_request(request=request)
        return cls.check_request(
            response=response,
            failure_message=f"Failed to get statements from moalmanac api at {root_url}"
        )


class SQL:
    @classmethod
    def add_about(cls, record, documents, session):
        about = models.About(
            last_updated=record.get('last_updated'),
            release=record.get('release'),
            documents_count=len(documents),
            propositions_count=record.get('propositions_count'),
            statements_count=record.get('statements_count')
        )
        session.add(about)

    @classmethod
    def add_biomarkers(cls, records, session):
        for record in records:
            biomarker_type = []
            biomarker = models.Biomarkers(
                id=record.get('id'),
                name=record.get('name'),
                type=record.get('biomarker_type'),
                propositions_count=record.get('propositions_count'),
                statements_count=record.get('statements_count')
            )
            session.add(biomarker)
            session.commit()

    @classmethod
    def add_diseases(cls, records, session):
        for record in records:
            disease = models.Diseases(
                id=record.get('id'),
                name=record.get('name'),
                propositions_count=record.get('propositions_count'),
                statements_count=record.get('statements_count')
            )
            session.add(disease)

    @classmethod
    def add_documents(cls, records, session):
        for record in records:
            document = models.Documents(
                id=record.get('id'),
                name=record.get('name'),
                citation=record.get('citation'),
                url=record.get('url'),
                organization_id=record.get('organization_id'),
                organization_name=record.get('organization_name'),
                indications_count=record.get('indications_count'),
                statements_count=record.get('statements_count')
            )
            session.add(document)

    @classmethod
    def add_genes(cls, records, session):
        for record in records:
            gene = models.Genes(
                id=record.get('id'),
                name=record.get('name'),
                biomarkers_count=record.get('biomarkers_count'),
                propositions_count=record.get('propositions_count'),
                statements_count=record.get('statements_count')
            )
            session.add(gene)

    @classmethod
    def add_indications(cls, records, session):
        for record in records:
            indication = models.Indications(
                id=record.get('id'),
                name=record.get('name'),
                document_id=record.get('document_id'),
                organization_id=record.get('organization_id'),
                organization_name=record.get('organization_name'),
                statements_count=record.get('statements_count')
            )
            session.add(indication)

    @classmethod
    def add_terms(cls, results, session):
        tables = [
            'biomarkers',
            'diseases',
            'documents',
            'genes',
            'therapies'
        ]
        count = 0
        for table in tables:
            for record in results[table]:
                term = models.Terms(
                    id=count,
                    table=table,
                    record_id=record.get('id'),
                    record_name=record.get('name')
                )
                session.add(term)
                count += 1

    @classmethod
    def add_therapies(cls, records, session):
        for record in records:
            therapy = models.Therapies(
                id=record.get('id'),
                name=record.get('name'),
                therapy_type=record.get('therapy_type'),
                propositions_count=record.get('propositions_count'),
                statements_count=record.get('statements_count')
            )
            session.add(therapy)


class Service:
    @classmethod
    def get(cls, api):
        response = Requests.get_service(root_url=api)
        if response.status_code == 200:
            return response.json()['service']
        else:
            return f"Something went wrong getting service from {api}."


class Statements:
    @staticmethod
    def make_organization_filter(settings):
        return [f'organization={agency.replace(" ", "%20")}' for agency, value in settings.items() if value == 'true']

    @classmethod
    def get(cls, agency_preferences, api):
        filters = cls.make_organization_filter(settings=agency_preferences)
        response = Requests.get_statements(root_url=api, filters=filters)
        if response.status_code == 200:
            return response.json()['data']
        else:
            return f"Something went wrong getting statements from {api} with filters: {filters}"


def main(config_path, api_url="https://api.moalmanac.org", drop=False):
    app = create_app(config_path=config_path)
    with app.app_context():
        config = database.read_config_ini(path=config_path)
        about = Service.get(api=api_url)
        statements = Statements.get(agency_preferences=config['agencies'], api=api_url)
        results = Process.statements(records=statements)
        about['propositions_count'] = results['propositions_count']
        about['statements_count'] = results['statements_count']

        session = flask.current_app.config['SESSION_FACTORY']()
        try:
            SQL.add_about(record=about, documents=results['documents'], session=session)
            session.commit()

            SQL.add_biomarkers(records=results['biomarkers'], session=session)
            session.commit()

            SQL.add_diseases(records=results['diseases'], session=session)
            session.commit()

            SQL.add_documents(records=results['documents'], session=session)
            session.commit()

            SQL.add_genes(records=results['genes'], session=session)
            session.commit()

            SQL.add_indications(records=results['indications'], session=session)
            session.commit()

            SQL.add_therapies(records=results['therapies'], session=session)
            session.commit()

            SQL.add_terms(results=results, session=session)
            session.commit()
        except Exception as e:
            print(f"Error occurred: {e}")
            session.rollback()
        finally:
            session.close()
            return 'Success!'


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        prog='Populate web browser sqlite cache(s) from moalmanac api',
        description='Using moalmanac API, populate sqlite3 db for each config'
    )
    arg_parser.add_argument(
        '-a', '--api',
        choices=['http://localhost:8000', 'https://api.moalmanac.org'],
        default='https://api.moalmanac.org',
        help='URL for the MOAlmanac API'
    )
    arg_parser.add_argument(
        '-c', '--config',
        help='Path to config file',
        required=True
    )
    arg_parser.add_argument(
        '-d', '--drop-tables',
        help='Drop tables before populating',
        action='store_true'
    )
    args = arg_parser.parse_args()
    main(
        config_path=args.config,
        api_url=args.api,
        drop=args.drop_tables
    )
