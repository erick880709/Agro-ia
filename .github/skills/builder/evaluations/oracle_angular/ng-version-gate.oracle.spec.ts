import { TestBed } from '@angular/core/testing';
import { ProfileForm } from './profile/profile-form';

async function setup() {
  const fixture = TestBed.createComponent(ProfileForm);
  const emitted: unknown[] = [];
  fixture.componentInstance.saved.subscribe((v) => emitted.push(v));
  await fixture.whenStable();
  const el: HTMLElement = fixture.nativeElement;
  const type = async (id: string, value: string) => {
    const input = el.querySelector(`[data-testid="${id}"]`) as HTMLInputElement | null;
    expect(input, `missing input ${id}`).toBeTruthy();
    input!.value = value;
    input!.dispatchEvent(new Event('input'));
    await fixture.whenStable();
  };
  const submit = async () => {
    el.querySelector('form')!.dispatchEvent(new Event('submit'));
    await fixture.whenStable();
  };
  return { emitted, type, submit };
}

describe('Oracle ProfileForm', () => {
  it('exige teléfono de 10 dígitos e incluye phone en saved', async () => {
    const { emitted, type, submit } = await setup();
    await type('name', 'Ana');
    await type('email', 'ana@bank.test');
    await submit();
    expect(emitted).toEqual([]);
    await type('phone', '30012345');
    await submit();
    expect(emitted).toEqual([]);
    await type('phone', '300123456a');
    await submit();
    expect(emitted).toEqual([]);
    await type('phone', '3001234567');
    await submit();
    expect(emitted).toEqual([{ name: 'Ana', email: 'ana@bank.test', phone: '3001234567' }]);
  });
  it('conserva las validaciones existentes', async () => {
    const { emitted, type, submit } = await setup();
    await type('name', 'Ana');
    await type('email', 'no-es-correo');
    await type('phone', '3001234567');
    await submit();
    expect(emitted).toEqual([]);
  });
});
