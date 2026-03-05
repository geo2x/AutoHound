"""Tests for Neo4j ingestor."""

import pytest
from unittest.mock import MagicMock, patch, call
from autohound.ingestor.neo4j_ingestor import Neo4jIngestor
from autohound.models import Graph, NodeType, EdgeType


def make_mock_record(data: dict):
    """Create a mock Neo4j record."""
    # Create a simple class that mimics Neo4j record behavior
    class MockRecord:
        def __init__(self, data_dict):
            self._data = data_dict
        
        def __getitem__(self, key):
            return self._data[key]
        
        def get(self, key, default=None):
            return self._data.get(key, default)
        
        def data(self):
            return self._data
    
    return MockRecord(data)


class TestNeo4jIngestor:
    """Test suite for Neo4jIngestor."""

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_connect_success(self, mock_graphdb):
        """Test successful connection to Neo4j."""
        mock_driver = MagicMock()
        mock_graphdb.driver.return_value = mock_driver
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        ingestor.connect()
        
        mock_graphdb.driver.assert_called_once_with(
            "bolt://localhost:7687",
            auth=("neo4j", "password")
        )
        mock_driver.verify_connectivity.assert_called_once()
        assert ingestor.driver == mock_driver

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_connect_failure(self, mock_graphdb):
        """Test connection failure."""
        mock_graphdb.driver.side_effect = Exception("Connection failed")
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        
        with pytest.raises(Exception, match="Connection failed"):
            ingestor.connect()

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_close(self, mock_graphdb):
        """Test closing connection."""
        mock_driver = MagicMock()
        mock_graphdb.driver.return_value = mock_driver
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        ingestor.connect()
        ingestor.close()
        
        mock_driver.close.assert_called_once()

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_context_manager(self, mock_graphdb):
        """Test context manager calls connect and close."""
        mock_driver = MagicMock()
        mock_graphdb.driver.return_value = mock_driver
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        
        with ingestor:
            mock_driver.verify_connectivity.assert_called_once()
        
        mock_driver.close.assert_called_once()

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_ingest_users(self, mock_graphdb):
        """Test user node ingestion."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_graphdb.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock user records - flat structure as returned by Cypher query
        user_records = [
            make_mock_record({
                'id': 'S-1-5-21-123-456-789-1001',
                'name': 'jdoe@domain.com',
                'enabled': True,
                'admincount': False,
                'domain': 'domain.com',
                'dn': 'CN=jdoe,DC=domain,DC=com',
                'labels': ['User']
            })
        ]
        mock_session.run.return_value = user_records
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        ingestor.connect()
        
        graph = Graph()
        ingestor._ingest_users(mock_session, graph)
        
        assert graph.node_count() == 1
        node = graph.get_node('S-1-5-21-123-456-789-1001')
        assert node is not None
        assert node.node_type == NodeType.USER
        assert node.name == 'jdoe@domain.com'

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_ingest_computers_with_dc(self, mock_graphdb):
        """Test computer ingestion including domain controller detection."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_graphdb.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock computer records including a DC
        computer_records = [
            make_mock_record({
                'id': 'S-1-5-21-123-456-789-1002',
                'name': 'DC01.DOMAIN.COM',
                'enabled': True,
                'domain': 'domain.com',
                'dn': 'CN=DC01,OU=Domain Controllers,DC=domain,DC=com',
                'unconstrained': False,
                'labels': ['Computer']
            }),
            make_mock_record({
                'id': 'S-1-5-21-123-456-789-1003',
                'name': 'WORKSTATION01.CORP.LOCAL',
                'enabled': True,
                'domain': 'corp.local',
                'dn': 'CN=WORKSTATION01,DC=corp,DC=local',
                'unconstrained': False,
                'labels': ['Computer']
            })
        ]
        mock_session.run.return_value = computer_records
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        ingestor.connect()
        
        graph = Graph()
        ingestor._ingest_computers(mock_session, graph)
        
        assert graph.node_count() == 2
        dc_node = graph.get_node('S-1-5-21-123-456-789-1002')
        assert dc_node.is_domain_controller
        assert dc_node.is_tier_zero
        
        ws_node = graph.get_node('S-1-5-21-123-456-789-1003')
        assert not ws_node.is_domain_controller

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_ingest_groups_high_value(self, mock_graphdb):
        """Test group ingestion with high-value group detection."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_graphdb.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock high-value group records
        group_records = [
            make_mock_record({
                'id': 'S-1-5-21-123-456-789-512',
                'name': 'DOMAIN ADMINS@DOMAIN.COM',
                'admincount': True,
                'domain': 'domain.com',
                'dn': 'CN=Domain Admins,CN=Users,DC=domain,DC=com'
            }),
            make_mock_record({
                'id': 'S-1-5-21-123-456-789-519',
                'name': 'ENTERPRISE ADMINS@DOMAIN.COM',
                'admincount': True,
                'domain': 'domain.com',
                'dn': 'CN=Enterprise Admins,CN=Users,DC=domain,DC=com'
            }),
            make_mock_record({
                'id': 'S-1-5-21-123-456-789-544',
                'name': 'ADMINISTRATORS@DOMAIN.COM',
                'admincount': True,
                'domain': 'domain.com',
                'dn': 'CN=Administrators,CN=Builtin,DC=domain,DC=com'
            }),
            make_mock_record({
                'id': 'S-1-5-21-123-456-789-518',
                'name': 'SCHEMA ADMINS@DOMAIN.COM',
                'admincount': True,
                'domain': 'domain.com',
                'dn': 'CN=Schema Admins,CN=Users,DC=domain,DC=com'
            }),
            make_mock_record({
                'id': 'S-1-5-21-123-456-789-548',
                'name': 'ACCOUNT OPERATORS@DOMAIN.COM',
                'admincount': True,
                'domain': 'domain.com',
                'dn': 'CN=Account Operators,CN=Builtin,DC=domain,DC=com'
            })
        ]
        mock_session.run.return_value = group_records
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        ingestor.connect()
        
        graph = Graph()
        ingestor._ingest_groups(mock_session, graph)
        
        # Check Domain Admins
        da_node = graph.get_node('S-1-5-21-123-456-789-512')
        assert da_node.is_domain_admin
        assert da_node.is_tier_zero
        
        # Check Enterprise Admins
        ea_node = graph.get_node('S-1-5-21-123-456-789-519')
        assert ea_node.is_enterprise_admin
        assert ea_node.is_tier_zero
        
        # Check Administrators
        admin_node = graph.get_node('S-1-5-21-123-456-789-544')
        assert admin_node.is_tier_zero
        
        # Check Schema Admins
        schema_node = graph.get_node('S-1-5-21-123-456-789-518')
        assert schema_node.is_tier_zero
        
        # Check Account Operators
        acct_node = graph.get_node('S-1-5-21-123-456-789-548')
        assert acct_node.is_tier_zero

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_ingest_domains(self, mock_graphdb):
        """Test domain ingestion marks nodes as tier zero."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_graphdb.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        domain_records = [
            make_mock_record({
                'id': 'S-1-5-21-123-456-789',
                'name': 'DOMAIN.COM'
            })
        ]
        mock_session.run.return_value = domain_records
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        ingestor.connect()
        
        graph = Graph()
        ingestor._ingest_domains(mock_session, graph)
        
        domain_node = graph.get_node('S-1-5-21-123-456-789')
        assert domain_node.is_tier_zero

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_ingest_gpos(self, mock_graphdb):
        """Test GPO ingestion."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_graphdb.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        gpo_records = [
            make_mock_record({
                'id': '{12345678-1234-1234-1234-123456789012}',
                'name': 'Default Domain Policy'
            })
        ]
        mock_session.run.return_value = gpo_records
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        ingestor.connect()
        
        graph = Graph()
        ingestor._ingest_gpos(mock_session, graph)
        
        assert graph.node_count() == 1
        gpo_node = graph.get_node('{12345678-1234-1234-1234-123456789012}')
        assert gpo_node.node_type == NodeType.GPO

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_ingest_ous(self, mock_graphdb):
        """Test OU ingestion."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_graphdb.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        ou_records = [
            make_mock_record({
                'id': 'OU=Users,DC=domain,DC=com',
                'name': 'Users'
            })
        ]
        mock_session.run.return_value = ou_records
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        ingestor.connect()
        
        graph = Graph()
        ingestor._ingest_ous(mock_session, graph)
        
        assert graph.node_count() == 1
        ou_node = graph.get_node('OU=Users,DC=domain,DC=com')
        assert ou_node.node_type == NodeType.OU

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_ingest_relationships(self, mock_graphdb):
        """Test relationship ingestion."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_graphdb.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # First call returns relationship types
        # Subsequent calls return relationships for each type
        rel_type_records = [
            make_mock_record({'rel_type': 'MemberOf'}),
            make_mock_record({'rel_type': 'AdminTo'})
        ]
        
        memberof_records = [
            make_mock_record({
                'source_id': 'S-1-5-21-123-456-789-1001',
                'target_id': 'S-1-5-21-123-456-789-512',
                'edge_type': 'MemberOf',
                'props': {}
            })
        ]
        
        adminto_records = [
            make_mock_record({
                'source_id': 'S-1-5-21-123-456-789-1001',
                'target_id': 'S-1-5-21-123-456-789-1002',
                'edge_type': 'AdminTo',
                'props': {}
            })
        ]
        
        mock_session.run.side_effect = [
            rel_type_records,
            memberof_records,
            adminto_records
        ]
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        ingestor.connect()
        
        # Add nodes first
        graph = Graph()
        from autohound.models import Node
        graph.add_node(Node('S-1-5-21-123-456-789-1001', 'user1', NodeType.USER))
        graph.add_node(Node('S-1-5-21-123-456-789-512', 'DA', NodeType.GROUP))
        graph.add_node(Node('S-1-5-21-123-456-789-1002', 'server1', NodeType.COMPUTER))
        
        ingestor._ingest_relationships(mock_session, graph)
        
        assert graph.edge_count() == 2

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_ingest_relationship_type(self, mock_graphdb):
        """Test ingestion of a specific relationship type."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_graphdb.driver.return_value = mock_driver
        
        rel_records = [
            make_mock_record({
                'source_id': 'S-1-5-21-123-456-789-1001',
                'target_id': 'S-1-5-21-123-456-789-1002',
                'edge_type': 'AdminTo',
                'props': {}
            })
        ]
        mock_session.run.return_value = rel_records
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        ingestor.driver = mock_driver
        
        graph = Graph()
        from autohound.models import Node
        graph.add_node(Node('S-1-5-21-123-456-789-1001', 'user1', NodeType.USER))
        graph.add_node(Node('S-1-5-21-123-456-789-1002', 'server1', NodeType.COMPUTER))
        
        ingestor._ingest_relationship_type(mock_session, graph, 'AdminTo')
        
        assert graph.edge_count() == 1

    def test_map_edge_type_all_mappings(self):
        """Test all edge type mappings."""
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        
        # Test all known mappings from the actual code
        assert ingestor._map_edge_type('MemberOf') == EdgeType.MEMBER_OF
        assert ingestor._map_edge_type('AdminTo') == EdgeType.ADMIN_TO
        assert ingestor._map_edge_type('HasSession') == EdgeType.HAS_SESSION
        assert ingestor._map_edge_type('CanRDP') == EdgeType.CAN_RDP
        assert ingestor._map_edge_type('CanPSRemote') == EdgeType.CAN_PS_REMOTE
        assert ingestor._map_edge_type('GenericAll') == EdgeType.GENERIC_ALL
        assert ingestor._map_edge_type('GenericWrite') == EdgeType.GENERIC_WRITE
        assert ingestor._map_edge_type('WriteOwner') == EdgeType.WRITE_OWNER
        assert ingestor._map_edge_type('WriteDacl') == EdgeType.WRITE_DACL
        assert ingestor._map_edge_type('AddMember') == EdgeType.ADD_MEMBER
        assert ingestor._map_edge_type('ForceChangePassword') == EdgeType.FORCE_CHANGE_PASSWORD
        assert ingestor._map_edge_type('AddAllowedToAct') == EdgeType.ADD_ALLOWED_TO_ACT
        assert ingestor._map_edge_type('DCSync') == EdgeType.DCSYNC
        assert ingestor._map_edge_type('GetChanges') == EdgeType.GET_CHANGES
        assert ingestor._map_edge_type('GetChangesAll') == EdgeType.GET_CHANGES_ALL
        assert ingestor._map_edge_type('GpLink') == EdgeType.GPO_APPLY
        assert ingestor._map_edge_type('AllowedToDelegate') == EdgeType.ALLOWED_TO_DELEGATE
        assert ingestor._map_edge_type('AllowedToAct') == EdgeType.ALLOWED_TO_ACT
        assert ingestor._map_edge_type('Contains') == EdgeType.CONTAINS
        assert ingestor._map_edge_type('TrustedBy') == EdgeType.TRUSTED_BY
        
        # Test unknown type returns UNKNOWN
        assert ingestor._map_edge_type('UnknownRelType') == EdgeType.UNKNOWN

    def test_sanitize_rel_type_valid(self):
        """Test sanitization of valid relationship types."""
        # Already tested in test_ingestor.py, but verify here
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        
        assert ingestor._sanitize_rel_type('MemberOf') == 'MemberOf'
        assert ingestor._sanitize_rel_type('AdminTo') == 'AdminTo'
        assert ingestor._sanitize_rel_type('GENERIC_ALL') == 'GENERIC_ALL'
        assert ingestor._sanitize_rel_type('Has_Session') == 'Has_Session'

    def test_sanitize_rel_type_invalid(self):
        """Test rejection of invalid relationship types."""
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        
        with pytest.raises(ValueError):
            ingestor._sanitize_rel_type('DROP TABLE;')
        
        with pytest.raises(ValueError):
            ingestor._sanitize_rel_type('Evil`Injection')
        
        with pytest.raises(ValueError):
            ingestor._sanitize_rel_type('')
        
        with pytest.raises(ValueError):
            ingestor._sanitize_rel_type('Unicode™Char')

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_ingest_full_pipeline(self, mock_graphdb):
        """Test full ingestion pipeline."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_graphdb.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock all query results
        user_records = [make_mock_record({'id': 'U1', 'name': 'user1'})]
        computer_records = [make_mock_record({'id': 'C1', 'name': 'comp1'})]
        group_records = [make_mock_record({'id': 'G1', 'name': 'group1'})]
        domain_records = [make_mock_record({'id': 'D1', 'name': 'domain.com'})]
        gpo_records = [make_mock_record({'id': 'GPO1', 'name': 'gpo1'})]
        ou_records = [make_mock_record({'id': 'OU1', 'name': 'ou1'})]
        rel_type_records = [make_mock_record({'rel_type': 'MemberOf'})]
        rel_records = [make_mock_record({'source_id': 'U1', 'target_id': 'G1', 'edge_type': 'MemberOf', 'props': {}})]
        
        mock_session.run.side_effect = [
            user_records, computer_records, group_records,
            domain_records, gpo_records, ou_records,
            rel_type_records, rel_records
        ]
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        graph = ingestor.ingest()
        
        assert graph.node_count() == 6
        assert graph.edge_count() == 1

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_ingest_auto_connects(self, mock_graphdb):
        """Test that ingest auto-connects if not already connected."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_graphdb.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock empty results
        mock_session.run.return_value = []
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        # Don't call connect() manually
        graph = ingestor.ingest()
        
        # Verify connect was called
        mock_driver.verify_connectivity.assert_called()
        assert graph is not None

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_ingest_driver_none_raises(self, mock_graphdb):
        """Test RuntimeError when driver is None after connect attempt."""
        # Mock driver that raises on verify_connectivity
        mock_driver = MagicMock()
        mock_driver.verify_connectivity.side_effect = Exception("Connection failed")
        mock_graphdb.driver.return_value = mock_driver
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        
        with pytest.raises(Exception, match="Connection failed"):
            ingestor.ingest()

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_ingest_users_with_domain_admin_in_name(self, mock_graphdb):
        """Test user with 'Domain Admin' in name gets marked as high-value."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_graphdb.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        user_records = [
            make_mock_record({
                'id': 'S-1-5-21-123-456-789-500',
                'name': 'Domain Admins Account',
                'enabled': True,
                'admincount': True,
                'domain': 'domain.com',
                'dn': 'CN=DA,DC=domain,DC=com',
                'labels': ['User']
            })
        ]
        mock_session.run.return_value = user_records
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        ingestor.connect()
        
        graph = Graph()
        ingestor._ingest_users(mock_session, graph)
        
        user = graph.get_node('S-1-5-21-123-456-789-500')
        assert user.is_domain_admin
        assert user.is_tier_zero

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_ingest_computers_with_domain_in_name(self, mock_graphdb):
        """Test computer with 'DOMAIN' in name gets marked as DC."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_graphdb.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        computer_records = [
            make_mock_record({
                'id': 'S-1-5-21-123-456-789-1004',
                'name': 'DOMAIN-CONTROLLER.CORP.LOCAL',
                'enabled': True,
                'domain': 'corp.local',
                'dn': 'CN=DOMAIN-CONTROLLER,DC=corp,DC=local',
                'unconstrained': False,
                'labels': ['Computer']
            })
        ]
        mock_session.run.return_value = computer_records
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        ingestor.connect()
        
        graph = Graph()
        ingestor._ingest_computers(mock_session, graph)
        
        comp = graph.get_node('S-1-5-21-123-456-789-1004')
        assert comp.is_domain_controller
        assert comp.is_tier_zero

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_ingest_without_driver(self, mock_graphdb):
        """Test that ingest returns empty graph when driver fails to connect."""
        mock_graphdb.driver.side_effect = Exception("Cannot connect")
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        
        with pytest.raises(Exception, match="Cannot connect"):
            ingestor.ingest()

    @patch('autohound.ingestor.neo4j_ingestor.GraphDatabase')
    def test_ingest_relationships_no_nodes(self, mock_graphdb):
        """Test relationship ingestion when source/target nodes don't exist."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_graphdb.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        rel_type_records = [make_mock_record({'rel_type': 'MemberOf'})]
        rel_records = [
            make_mock_record({
                'source_id': 'NONEXISTENT1',
                'target_id': 'NONEXISTENT2',
                'edge_type': 'MemberOf',
                'props': {}
            })
        ]
        
        mock_session.run.side_effect = [rel_type_records, rel_records]
        
        ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
        ingestor.connect()
        
        graph = Graph()
        # Edges are added even if nodes don't exist
        ingestor._ingest_relationships(mock_session, graph)
        
        # Edge should still be added (graph doesn't validate node existence)
        assert graph.edge_count() == 1
