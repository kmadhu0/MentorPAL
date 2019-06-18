import React from 'react'
import PropTypes from 'prop-types'
import classNames from 'classnames'
import FlipMove from 'react-flip-move';
import { useSelector, useDispatch } from 'react-redux';
import { Button, List, ListItem } from '@material-ui/core'
import { withStyles, MuiThemeProvider, createMuiTheme } from '@material-ui/core/styles'

import { sendQuestion } from '../redux/actions'

const Questions = ({ ...props }) => {
  const { classes } = props;
  const dispatch = useDispatch()
  const current_topic = useSelector(state => state.current_topic)
  const mentor = useSelector(state => state.mentors_by_id[state.current_mentor])

  if (!mentor || !mentor.topic_questions || !mentor.topic_questions[current_topic]) {
    return <div></div>
  }

  const questions = mentor.topic_questions[current_topic]
  const height = document.getElementById('question-container').clientHeight
  const onQuestionSelected = (question) => {
    dispatch(sendQuestion(question))
  }

  return (
    <MuiThemeProvider theme={theme}>
      <List style={{ maxHeight: height * 0.9, overflow: 'auto' }}>
        <FlipMove>
          {questions.map((question, i) =>
            <ListItem key={i}>
              <Button
                className={classNames(classes.button)}
                onClick={() => onQuestionSelected(question)}>
                {question}
              </Button>
            </ListItem>
          )}
        </FlipMove>
      </List>
    </MuiThemeProvider>
  )
}

const styles = ({
  button: {
    textTransform: 'none',
    textAlign: 'left',
  },
});

const theme = createMuiTheme({
  palette: {
    primary: { main: '#1B6A9C' },
  },
  typography: { useNextVariants: true },
});

Questions.propTypes = {
  classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(Questions);