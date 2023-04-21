import React, { useState } from 'react';
import {
  Form, Button, Container, Accordion, Modal,
} from 'react-bootstrap';
import OutputLog from '../components/OutputLog';
import Info from '../components/Info';

export default () => {
  const [help, setHelp] = useState(null);
  const [jobId, setJobId] = useState(window.localStorage.getItem('last-jobid'));
  const [formData, setFormData] = useState({
    githubPat: '',
    slug: '',
    projId: '',
  });

  // eslint-disable-next-line max-len
  const isValidState = () => !!formData.githubPat.length && !!formData.slug.length && !!formData.projId.length;
  const delimHelp = (evt) => {
    evt.preventDefault();
    setHelp((
      <div>
        <p>
          This is the splitter between parts of the filename. Geolosys uses format
          {' '}
          <code>MODNAME-MCVER-MAJOR.MINOR.PATCH</code>
          , where
          {' '}
          <code>-</code>
          {' '}
          is the delimiter.
        </p>
        <p>
          Using this logic, it is assumed that the Minecraft version for this
          {' '}
          <code>.jar</code>
          -file is between the first and second delimiter, and that the mod version is between
          the second and the end of the file. Formatting aside from this is not supported,
          unfortunately, as I&apos;ve got a bit of trauma
          {' '}
          <sup>(/s)</sup>
          {' '}
          from
          {' '}
          <a href="https://dv2ls.com/code?id=lUY-c4A2H" target="_blank" rel="noreferrer">
            this Regular Expression I wrote.
          </a>
        </p>
      </div>
    ));
  };

  const makeJob = async (evt) => {
    evt.preventDefault();
    if (!isValidState()) return;

    const resp = await fetch('/jobs/new', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });

    if (resp && resp.ok) {
      const data = await resp.text();
      setJobId(data);
      window.localStorage.setItem('last-jobid', data);
    }
  };

  return (
    <div style={{ margin: 'auto', maxWidth: '768px' }}>
      <h2 className="mb-4 text-center">
        CurseForge to Modrinth Mod Migrator (CTMMM)
      </h2>

      {!window.localStorage.getItem('info-dismissed') && (<Info />)}

      <Container style={{ margin: '1rem auto', maxWidth: '512px' }}>
        <Form onSubmit={makeJob} className="juse-form">
          <Form.Group className="mb-3" controlId="githubPat">
            <Form.Label>GitHub Personal Access Token</Form.Label>
            <Form.Control
              type="password"
              required
              placeholder="This field is required"
              value={formData.githubPat}
              onChange={(x) => setFormData({
                ...formData,
                githubPat: x.target.value,
              })}
            />
            <Form.Text className="text-muted">
              This value is encrypted from end-to-end and even in storage
            </Form.Text>
          </Form.Group>

          <Form.Group className="mb-3" controlId="slug">
            <Form.Label>CurseForge Project Slug</Form.Label>
            <Form.Control
              type="text"
              required
              placeholder="This field is required"
              value={formData.slug}
              onChange={(x) => setFormData({
                ...formData,
                slug: x.target.value,
              })}
            />
          </Form.Group>

          <Form.Group className="mb-3" controlId="projId">
            <Form.Label>Modrinth Project ID</Form.Label>
            <Form.Control
              type="text"
              required
              placeholder="This field is required"
              value={formData.projId}
              onChange={(x) => setFormData({
                ...formData,
                projId: x.target.value,
              })}
            />
          </Form.Group>

          <Form.Group className="mb-3" controlId="delimiter">
            <Form.Label>
              Delimiter (Optional)
              {' '}
              {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
              <a onClick={delimHelp} style={{ textDecoration: 'none' }} href="#">❔</a>
            </Form.Label>
            <Form.Control
              placeholder="Defaults to Hyphen (-)"
              type="text"
              value={formData.delimiter}
              onChange={(x) => setFormData({
                ...formData,
                delimiter: x.target.value,
              })}
            />
          </Form.Group>

          <Button
            variant="success"
            type="submit"
            disabled={!isValidState()}
          >
            Submit
          </Button>
        </Form>

        {jobId && (
        <Accordion defaultActiveKey="0" className="mt-2">
          <Accordion.Item eventKey="1">
            <Accordion.Header>
              <div>
                Status &amp; Output Log for Job
                {' '}
                <code>{`#${jobId}`}</code>
              </div>
            </Accordion.Header>
            <Accordion.Body>{jobId && (<OutputLog id={jobId} />)}</Accordion.Body>
          </Accordion.Item>
        </Accordion>
        )}
      </Container>

      <Modal centered show={!!help} onHide={() => setHelp(null)}>
        <Modal.Body>{help}</Modal.Body>
      </Modal>
    </div>
  );
};
