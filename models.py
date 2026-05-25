# Add to RelationshipEdge or PersonNode table
class SpatioTemporalIndex(Base):
    __tablename__ = "spatial_temporal_indices"
    
    index_id = Column(String(36), primary_key=True)
    person_id = Column(String(36), ForeignKey("person_nodes.person_id"))
    geocode_cluster = Column(String(50), index=True) # H3 spatial index or county string
    time_window_start = Column(Integer)             # Year format: e.g., 1850
    time_window_end = Column(Integer)               # Year format: e.g., 1875
  
