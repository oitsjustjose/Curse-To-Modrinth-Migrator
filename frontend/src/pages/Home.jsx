/* eslint-disable import/no-extraneous-dependencies */
import React, { useState, useEffect } from 'react';
import {
  Form, Button, Container, Accordion, Image,
} from 'react-bootstrap';
import { TbInfoHexagon, TbHelp } from 'react-icons/tb';
import OutputLog from '../components/OutputLog';
import Info from '../components/Help/Info';
import HeaderImg from '../img/ctm.png';
import ModrinthProjId from '../components/Help/ModrinthProjId';
import { CreateModrinthUri, ModrinthOauthCallbackHandler } from '../shared';

export default () => {
  const [dark, setDark] = useState(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
  const [modals, setModals] = useState({ info: false, mpid: false });
  const [jobId, setJobId] = useState(window.localStorage.getItem('last-jobid'));
  const [formData, setFormData] = useState({
    curseforgeSlug: '',
    modrinthId: '',
  });

  /*
    Begins the Modrinth OAuth flow, creating a URL with a callback that has the
      data we need in the query params and will return back with the client's
      oauth code that will be needed back on the backend. When the OAuth call
      succeeds, the callback will trigger the useEffect below to handle it.
  */
  const startOauthFlow = (evt) => {
    evt && evt.preventDefault();

    const uri = CreateModrinthUri(formData.curseforgeSlug, formData.modrinthId);
    window.location.href = uri;
  };

  useEffect(() => { // Handle the Modrinth OAuth callback
    const internalCreateJob = async (formDataIn) => {
      if (!formDataIn.code.length) return;
      if (!formDataIn.curseforgeSlug.length) return;
      if (!formDataIn.modrinthId.length) return;
      if (!formDataIn.redirectUri.length) return;

      const body = {
        clientOauthCode: formDataIn.code,
        curseforgeSlug: formDataIn.curseforgeSlug,
        modrinthId: formDataIn.modrinthId,
        redirectUri: formDataIn.redirectUri,
      };

      const resp = await fetch('/api/v1/jobs', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (resp && resp.ok) {
        const data = await resp.text();
        setJobId(data);
        window.localStorage.setItem('last-jobid', data);
      }
    };

    const newFormData = ModrinthOauthCallbackHandler();
    if (!newFormData) return () => { };

    internalCreateJob(newFormData);

    // Push state w/o URLQuery to avoid infinite reload of the page
    if (window.history.pushState) {
      const url = new URL(window.location.href);
      url.search = '';
      window.history.pushState({ path: url.toString() }, '', url.toString());
    }

    return () => { };
  }, [ModrinthOauthCallbackHandler]);

  useEffect(() => { // DARK MODE STUFF HERE
    // Set initial state before even bothering with the update state
    window.document.scrollingElement.setAttribute('data-bs-theme', dark ? 'dark' : 'light');

    const pref = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = (query) => {
      window.document.scrollingElement.setAttribute(
        'data-bs-theme',
        query.matches ? 'dark' : 'light',
      );
      setDark(query.matches);
    };

    pref.addEventListener('change', onChange);
    return () => pref.removeEventListener('change', onChange);
  }, [dark, setDark]);

  return (
    <div className="ctm-root">
      <Info
        dark={dark}
        override={modals.info}
        propagateOnHide={() => setModals({ ...modals, info: false })}
      />
      <ModrinthProjId show={modals.mpid} onHide={() => setModals({ ...modals, mpid: false })} />

      <Container style={{ margin: '1rem auto', maxWidth: '512px' }}>
        <Image className="d-block mb-3 mx-auto w-50 headerimg" src={HeaderImg} />
        <p className="text-center" style={{ fontSize: '1.25rem' }}>
          <b>C</b>
          urse
          {' '}
          <b>T</b>
          o
          {' '}
          <b>M</b>
          odrinth
          {' '}
          <b>M</b>
          od
          {' '}
          <b>M</b>
          igrator
        </p>
        <Form onSubmit={startOauthFlow} className="juse-form">
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
            <Form.Label>
              Modrinth Project ID
              {' '}
              <Button
                size="lg"
                className="anchor-disguised"
                onClick={() => setModals({ ...modals, mpid: true })}
                type="button"
                variant=""
              >
                <TbHelp fontSize="1.5rem" />
              </Button>
            </Form.Label>
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

          <Button variant={dark ? 'light' : 'dark'} type="submit">Submit</Button>
          <Button
            className="info"
            onClick={() => setModals({ ...modals, info: true })}
            variant={dark ? 'light' : 'dark'}
            type="button"
          >
            <TbInfoHexagon />
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
    </div>
  );
};
