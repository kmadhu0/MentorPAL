Feature: Serves mentor tracks

  Scenario Outline: request close-caption track data for a mentor
    Given a request url http://localhost:5000/mentor-api/mentors/<mentor>/tracks/<track_file>
      When the request sends GET
      Then the response status is OK
  
  Examples: MentorTracks
    | mentor    | track_file                          |
    | clint     | clintanderson_A1_1_1.txt            |
    | dan       | dandavis_A1_1_1.txt                 |
    | julianne  | julianne_A1_1_2.txt                 |
    