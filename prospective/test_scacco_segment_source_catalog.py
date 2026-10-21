from prospective.scacco_segment_source_catalog import audit_segments,find_member
import csv
import io
import zipfile
import pytest

NAMES=[
 "studyName","studyID","individualID","species","segmentID",
 "segm_timeStart","totNlocs","dataSource","avg_thermUplift",
 "avg_oroUplift","avg_windSpeed_1000m","avg_windSupp_1000m",
 "avg_probFlap","height_gener"
]

def reader(rows):
    x=io.StringIO();w=csv.DictWriter(x,fieldnames=NAMES);w.writeheader()
    for r in rows:w.writerow(r)
    x.seek(0);return csv.DictReader(x)

def record(bird,day,segment,study="studyA",nfix=21):
    return dict(studyName=study,studyID=study,individualID=bird,
      species="Species A",segmentID=segment,segm_timeStart=day+" 10:00:00",
      totNlocs=str(nfix),dataSource="Movebank",avg_thermUplift="1.2",
      avg_oroUplift=".3",avg_windSpeed_1000m="4",
      avg_windSupp_1000m="2",avg_probFlap=".4",height_gener="DO_NOT_READ")

def test_ten_birds_both_days_is_study_candidate_without_height():
    rows=[record(f"b{i}",day,f"s{i}-{day}") for i in range(10)
          for day in ("2016-05-01","2016-05-02")]
    a=audit_segments(reader(rows))
    assert a["candidate_taxa_ge10_birds"]==1
    assert a["candidate_panels_ge10_birds"]==1
    assert a["panels"][0]["eligible_birds_two_days_ge20_fixes"]==10
    assert a["panels"][0]["eligible_birds_two_days_each_2segments_ge20fixes"]==0
    assert not a["per_point_RDS_opened"]

def test_same_species_two_studies_count_as_two_panels():
    rows=[record(f"b{i}",day,f"{study}-{i}-{day}",study)
      for study in ("s1","s2") for i in range(10)
      for day in ("2016-05-01","2016-05-02")]
    a=audit_segments(reader(rows))
    assert a["candidate_panels_ge10_birds"]==2
    assert a["candidate_taxa_ge10_birds"]==1

def test_nineteen_fixes_day_is_insufficient():
    rows=[record(f"b{i}",day,f"s{i}-{day}",nfix=19)
      for i in range(10) for day in ("2016-05-01","2016-05-02")]
    a=audit_segments(reader(rows))
    assert a["candidate_panels_ge10_birds"]==0

def test_missing_environment_schema_is_not_filled_by_imputation():
    data=reader([record("b1","2016-05-01","s")])
    data.fieldnames=[x for x in data.fieldnames if x!="avg_thermUplift"]
    with pytest.raises(ValueError,match="schema missing"):
        audit_segments(data)

def test_zip_file_member_match_avoids_mac_redundant(tmp_path):
    f=tmp_path/"example.zip"
    with zipfile.ZipFile(f,"w") as z:
        z.writestr("Data/BiologgingData/FinalDf_perPoint_VedbaGs_flappingProbs_ENV.rds",b"RDS")
        z.writestr("__MACOSX/Data/BiologgingData/FinalDf_perPoint_VedbaGs_flappingProbs_ENV.rds",b"FAKE")
    with zipfile.ZipFile(f) as z:
        x=find_member(z.infolist(),"FinalDf_perPoint_VedbaGs_flappingProbs_ENV.rds")
    assert x.filename.startswith("Data/BiologgingData/")
