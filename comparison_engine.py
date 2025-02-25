import numpy as np
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
import logging

logger = logging.getLogger(__name__)

class ComparisonEngine:
    def __init__(self):
        self.differences = {
            'structural': {
                'entity_differences': {
                    'only_in_file1': {},
                    'only_in_file2': {},
                    'count_differences': {}
                },
                'relationship_differences': {
                    'only_in_file1': {},
                    'only_in_file2': {},
                    'count_differences': {}
                }
            },
            'pmi': {
                'only_in_file1': {},
                'only_in_file2': {},
                'value_differences': {}
            },
            'attributes': {
                'only_in_file1': {},
                'only_in_file2': {},
                'value_differences': {}
            },
            'geometric': {
                'volume': {
                    'file1': 0,
                    'file2': 0,
                    'difference': 0,
                    'percentage': 0
                },
                'surface_area': {
                    'file1': 0,
                    'file2': 0,
                    'difference': 0,
                    'percentage': 0
                },
                'center_of_mass': {
                    'file1': [0, 0, 0],
                    'file2': [0, 0, 0],
                    'distance': 0
                },
                'bounding_box': {
                    'file1': {
                        'dimensions': [0, 0, 0],
                        'volume': 0
                    },
                    'file2': {
                        'dimensions': [0, 0, 0],
                        'volume': 0
                    },
                    'difference': 0,
                    'percentage': 0
                }
            },
            'summary': {
                'total_differences': 0,
                'structural_differences': 0,
                'pmi_differences': 0,
                'attribute_differences': 0,
                'geometric_differences': 0,
                'similarity_score': 100  # Percentage
            }
        }
    
    def compare(self, data1, data2, step_file1=None, step_file2=None):
        """Compare two STEP-AP242 data structures and identify differences"""
        # Compare entity types and counts
        self._compare_entities(data1['entities'], data2['entities'])
        
        # Compare relationships
        self._compare_relationships(data1['relationships'], data2['relationships'])
        
        # Compare PMI data
        self._compare_pmi(data1['pmi_data'], data2['pmi_data'])
        
        # Compare other attributes
        self._compare_attributes(data1['attributes'], data2['attributes'])
        
        # Compare geometric properties if STEP files are provided
        if step_file1 and step_file2:
            self._compare_geometric_properties(step_file1, step_file2)
        
        # Calculate summary statistics
        self._calculate_summary()
        
        return self.differences
    
    def _compare_entities(self, entities1, entities2):
        """Compare entity types and counts between two models"""
        # Find entities only in file 1
        for entity_type, count in entities1.items():
            if entity_type not in entities2:
                self.differences['structural']['entity_differences']['only_in_file1'][entity_type] = count
            elif entities1[entity_type] != entities2[entity_type]:
                diff = entities1[entity_type] - entities2[entity_type]
                change = "+" + str(diff) if diff > 0 else str(diff)
                self.differences['structural']['entity_differences']['count_differences'][entity_type] = {
                    'file1': entities1[entity_type],
                    'file2': entities2[entity_type],
                    'change': change
                }
        
        # Find entities only in file 2
        for entity_type, count in entities2.items():
            if entity_type not in entities1:
                self.differences['structural']['entity_differences']['only_in_file2'][entity_type] = count
    
    def _compare_relationships(self, relationships1, relationships2):
        """Compare relationships between entities in two models"""
        # Implementation for comparing relationships
        # Similar to _compare_entities but for relationship data
        pass
    
    def _compare_pmi(self, pmi1, pmi2):
        """Compare Product and Manufacturing Information between two models"""
        # Implementation for comparing PMI data
        pass
    
    def _compare_attributes(self, attributes1, attributes2):
        """Compare attributes between two models"""
        # Implementation for comparing attributes
        pass
    
    def _compare_geometric_properties(self, step_file1, step_file2):
        """Compare geometric properties between two models"""
        try:
            # Load the STEP files
            shape1 = self._load_step_file(step_file1)
            shape2 = self._load_step_file(step_file2)
            
            if shape1 and shape2:
                # Calculate volume
                vol1 = self._calculate_volume(shape1)
                vol2 = self._calculate_volume(shape2)
                vol_diff = abs(vol1 - vol2)
                vol_pct = (vol_diff / max(vol1, vol2)) * 100 if max(vol1, vol2) > 0 else 0
                
                self.differences['geometric']['volume'] = {
                    'file1': vol1,
                    'file2': vol2,
                    'difference': vol_diff,
                    'percentage': vol_pct
                }
                
                # Calculate surface area
                area1 = self._calculate_surface_area(shape1)
                area2 = self._calculate_surface_area(shape2)
                area_diff = abs(area1 - area2)
                area_pct = (area_diff / max(area1, area2)) * 100 if max(area1, area2) > 0 else 0
                
                self.differences['geometric']['surface_area'] = {
                    'file1': area1,
                    'file2': area2,
                    'difference': area_diff,
                    'percentage': area_pct
                }
                
                # Calculate center of mass
                com1 = self._calculate_center_of_mass(shape1)
                com2 = self._calculate_center_of_mass(shape2)
                com_distance = np.linalg.norm(np.array(com1) - np.array(com2))
                
                self.differences['geometric']['center_of_mass'] = {
                    'file1': com1,
                    'file2': com2,
                    'distance': com_distance
                }
                
                # Calculate bounding box
                bbox1 = self._calculate_bounding_box(shape1)
                bbox2 = self._calculate_bounding_box(shape2)
                bbox_vol_diff = abs(bbox1['volume'] - bbox2['volume'])
                bbox_vol_pct = (bbox_vol_diff / max(bbox1['volume'], bbox2['volume'])) * 100 if max(bbox1['volume'], bbox2['volume']) > 0 else 0
                
                self.differences['geometric']['bounding_box'] = {
                    'file1': bbox1,
                    'file2': bbox2,
                    'difference': bbox_vol_diff,
                    'percentage': bbox_vol_pct
                }
            
        except Exception as e:
            logger.error(f"Error comparing geometric properties: {str(e)}")
    
    def _load_step_file(self, step_file):
        """Load a STEP file and return the shape"""
        try:
            step_reader = STEPControl_Reader()
            status = step_reader.ReadFile(step_file)
            
            if status == IFSelect_RetDone:
                step_reader.TransferRoots()
                shape = step_reader.Shape()
                return shape
            else:
                logger.error(f"Failed to read STEP file: {step_file}")
                return None
        except Exception as e:
            logger.error(f"Error loading STEP file: {str(e)}")
            return None
    
    def _calculate_volume(self, shape):
        """Calculate the volume of a shape"""
        try:
            props = GProp_GProps()
            brepgprop.VolumeProperties(shape, props)
            return props.Mass()
        except Exception as e:
            logger.error(f"Error calculating volume: {str(e)}")
            return 0
    
    def _calculate_surface_area(self, shape):
        """Calculate the surface area of a shape"""
        try:
            props = GProp_GProps()
            brepgprop.SurfaceProperties(shape, props)
            return props.Mass()
        except Exception as e:
            logger.error(f"Error calculating surface area: {str(e)}")
            return 0
    
    def _calculate_center_of_mass(self, shape):
        """Calculate the center of mass of a shape"""
        try:
            props = GProp_GProps()
            brepgprop.VolumeProperties(shape, props)
            com = props.CentreOfMass()
            return [com.X(), com.Y(), com.Z()]
        except Exception as e:
            logger.error(f"Error calculating center of mass: {str(e)}")
            return [0, 0, 0]
    
    def _calculate_bounding_box(self, shape):
        """Calculate the bounding box of a shape"""
        try:
            bbox = Bnd_Box()
            brepbndlib.Add(shape, bbox)
            
            xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
            
            dimensions = [
                abs(xmax - xmin),
                abs(ymax - ymin),
                abs(zmax - zmin)
            ]
            
            volume = dimensions[0] * dimensions[1] * dimensions[2]
            
            return {
                'dimensions': dimensions,
                'volume': volume
            }
        except Exception as e:
            logger.error(f"Error calculating bounding box: {str(e)}")
            return {
                'dimensions': [0, 0, 0],
                'volume': 0
            }
    
    def _calculate_summary(self):
        """Calculate summary statistics for the comparison"""
        # Count structural differences
        structural_diffs = (
            len(self.differences['structural']['entity_differences']['only_in_file1']) +
            len(self.differences['structural']['entity_differences']['only_in_file2']) +
            len(self.differences['structural']['entity_differences']['count_differences']) +
            len(self.differences['structural']['relationship_differences']['only_in_file1']) +
            len(self.differences['structural']['relationship_differences']['only_in_file2']) +
            len(self.differences['structural']['relationship_differences']['count_differences'])
        )
        
        # Count PMI differences
        pmi_diffs = (
            len(self.differences['pmi']['only_in_file1']) +
            len(self.differences['pmi']['only_in_file2']) +
            len(self.differences['pmi']['value_differences'])
        )
        
        # Count attribute differences
        attr_diffs = (
            len(self.differences['attributes']['only_in_file1']) +
            len(self.differences['attributes']['only_in_file2']) +
            len(self.differences['attributes']['value_differences'])
        )
        
        # Count geometric differences (based on percentage thresholds)
        geo_diffs = 0
        if self.differences['geometric']['volume']['percentage'] > 1:
            geo_diffs += 1
        if self.differences['geometric']['surface_area']['percentage'] > 1:
            geo_diffs += 1
        if self.differences['geometric']['center_of_mass']['distance'] > 0.1:
            geo_diffs += 1
        if self.differences['geometric']['bounding_box']['percentage'] > 1:
            geo_diffs += 1
        
        # Calculate total differences
        total_diffs = structural_diffs + pmi_diffs + attr_diffs + geo_diffs
        
        # Calculate similarity score (inverse of difference percentage)
        # This is a simplified calculation - you might want to weight different types of differences
        max_possible_diffs = 100  # Arbitrary maximum
        similarity_score = max(0, 100 - (total_diffs / max_possible_diffs * 100))
        
        # Update summary
        self.differences['summary'] = {
            'total_differences': total_diffs,
            'structural_differences': structural_diffs,
            'pmi_differences': pmi_diffs,
            'attribute_differences': attr_diffs,
            'geometric_differences': geo_diffs,
            'similarity_score': similarity_score
        } 