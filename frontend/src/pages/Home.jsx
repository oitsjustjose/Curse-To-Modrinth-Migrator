/* eslint-disable import/no-extraneous-dependencies */
import React, { useState } from 'react';
import {
  Form, Button, Container, Accordion, Image,
} from 'react-bootstrap';
import { TbInfoHexagon, TbHelp } from 'react-icons/tb';
import OutputLog from '../components/OutputLog';
import Info from '../components/Help/Info';
import Delimiter from '../components/Help/Delimiter';
import HeaderImg from '../img/ctm.png';

export default () => {
  const [modals, setModals] = useState({ info: false, delim: false });
  const [jobId, setJobId] = useState(window.localStorage.getItem('last-jobid'));
  const [formData, setFormData] = useState({
    githubPat: '',
    curseforgeSlug: '',
    modrinthId: '',
  });

  // eslint-disable-next-line max-len
  const isValidState = () => !!formData.githubPat.length && !!formData.curseforgeSlug.length && !!formData.modrinthId.length;

  const makeJob = async (evt) => {
    evt.preventDefault();
    if (!isValidState()) return;

    const resp = await fetch('/api/v1/jobs', {
      method: 'PUT',
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
    <div className="ctm-root">
      <Info override={modals.info} propagateOnHide={() => setModals({ ...modals, info: false })} />
      <Delimiter show={modals.delim} onHide={() => setModals({ ...modals, delim: false })} />

      <Container style={{ margin: '1rem auto', maxWidth: '512px' }}>
        <Image className="d-block mb-3 mx-auto w-50 " src={HeaderImg} />
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
              value={formData.curseforgeSlug}
              onChange={(x) => setFormData({
                ...formData,
                curseforgeSlug: x.target.value,
              })}
            />
          </Form.Group>

          <Form.Group className="mb-3" controlId="projId">
            <Form.Label>Modrinth Project ID</Form.Label>
            <Form.Control
              type="text"
              required
              placeholder="This field is required"
              value={formData.modrinthId}
              onChange={(x) => setFormData({
                ...formData,
                modrinthId: x.target.value,
              })}
            />
          </Form.Group>

          <Form.Group className="mb-3" controlId="delimiter">
            <Form.Label>
              Delimiter (Optional)
              {' '}
              {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
              <a
                onClick={() => setModals({ ...modals, delim: true })}
                style={{ textDecoration: 'none', fontSize: '16px' }}
                href="#"
                label="delimiter_help"
              >
                <TbHelp />
              </a>
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
            variant="dark"
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

      <Button
        onClick={() => setModals({ ...modals, info: true })}
        className="info"
        variant="dark"
      >
        <TbInfoHexagon ce />
      </Button>

      {/* <Modal centered show={!!help} onHide={() => setHelp(null)}>
        <Modal.Header closeButton>
          <Modal.Title>Help</Modal.Title>
        </Modal.Header>
        <Modal.Body>{help}</Modal.Body>
      </Modal> */}
    </div>
  );
};
