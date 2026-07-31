export const meta = {
  name: 'implement-story',
  description: 'Implement one user story against product/ via a python-implementer + code-reviewer loop, up to 3 attempts',
  phases: [
    { title: 'Load' },
    { title: 'Implement' },
    { title: 'Review' },
  ],
}

const MAX_ATTEMPTS = 3

// `args` sometimes arrives as a JSON-encoded string rather than the parsed object,
// even when passed as a real object to Workflow() — parse defensively either way.
const parsedArgs = typeof args === 'string' ? JSON.parse(args) : args
const storyId = parsedArgs.storyId

const STORY_SCHEMA = {
  type: 'object',
  properties: {
    title: { type: 'string' },
    body: { type: 'string' },
    criteria: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          text: { type: 'string' },
          done: { type: 'boolean' },
        },
        required: ['text', 'done'],
      },
    },
  },
  required: ['title', 'body', 'criteria'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    approved: { type: 'boolean' },
    issues: {
      type: 'array',
      items: { type: 'string' },
    },
  },
  required: ['approved', 'issues'],
}

phase('Load')
const story = await agent(
  `Read USER_STORIES.md at the repo root and find the story with id "${storyId}" ` +
  `(a "## ${storyId}: <title>" heading). Return its title, its full body text ` +
  `(the As a/I want/So that lines and any other prose, excluding the criteria checklist), ` +
  `and its acceptance criteria as a list of {text, done} objects where done is true only ` +
  `if the checkbox is "- [x]" rather than "- [ ]".`,
  { label: 'load-story', schema: STORY_SCHEMA }
)

const criteriaLines = story.criteria
  .map((c) => `- [${c.done ? 'x' : ' '}] ${c.text}`)
  .join('\n')
const taskPrompt = `Story ${storyId}: ${story.title}\n\n${story.body}\n\nAcceptance criteria:\n${criteriaLines}`

log(`Loaded ${storyId}: ${story.title}`)

let feedback = null
let approved = false
let lastReview = null
let attemptsUsed = 0

for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
  attemptsUsed = attempt
  log(`Attempt ${attempt}/${MAX_ATTEMPTS}`)

  const implPrompt = feedback
    ? `${taskPrompt}\n\nA previous attempt at this story was reviewed and needs revision. ` +
      `Address every point in this reviewer feedback:\n${feedback}`
    : taskPrompt

  await agent(implPrompt, {
    agentType: 'python-implementer',
    phase: 'Implement',
    label: `implement-attempt-${attempt}`,
  })

  const review = await agent(
    `${taskPrompt}\n\nReview the current state of product/ against every acceptance criterion above.`,
    {
      agentType: 'code-reviewer',
      phase: 'Review',
      label: `review-attempt-${attempt}`,
      schema: REVIEW_SCHEMA,
    }
  )

  lastReview = review
  log(`Review ${attempt}: ${review.approved ? 'approved' : `${review.issues.length} issue(s)`}`)

  if (review.approved) {
    approved = true
    break
  }
  feedback = review.issues.join('\n')
}

return {
  storyId,
  title: story.title,
  approved,
  attemptsUsed,
  lastReview,
}
